from datetime import datetime, timedelta
import os
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.empty import EmptyOperator
from dotenv import load_dotenv

load_dotenv("/opt/airflow/.env")

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "start_date": datetime(2023, 12, 1),
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "job_etl_pipeline",
    default_args=default_args,
    description="ETL Pipeline for Job Data (Crawl -> Kafka -> Spark Consumer -> DW)",
    schedule="@daily",  
    catchup=False,
) as dag:

    start_task = EmptyOperator(task_id="start")

    # Task 1: Crawl Data (Check/Verify crawl data exists)
    crawl_data = BashOperator(
        task_id="crawl_job_data",
        bash_command="python /opt/airflow/scripts/run_crawl.py",
        env={**os.environ, "PYTHONPATH": "/opt/airflow/apps"},
    )

    # Task 2: Produce to Kafka
    produce_kafka = BashOperator(
        task_id="produce_to_kafka",
        bash_command="python /opt/airflow/apps/crawler/kafka/producer.py",
        env={**os.environ, "PYTHONPATH": "/opt/airflow/apps", "KAFKA_BOOTSTRAP_SERVERS": "kafka:29092"},
    )

    # Task 3: Create unified_jobs table (if not exists)
    create_unified_jobs = BashOperator(
        task_id="create_unified_jobs_table",
        bash_command="python /opt/airflow/scripts/run_sql.py /opt/airflow/dags/sql/create_unified_jobs.sql",
        env={**os.environ},
    )

    # Task 4: Spark Consumer - Consume from Kafka and write to PostgreSQL
    
    spark_consumer = BashOperator(
        task_id="spark_consumer",
        bash_command="""
        sudo docker exec -u root spark-master bash -c "mkdir -p /home/spark/.ivy2/cache && chown -R spark:spark /home/spark/.ivy2" && \
        sudo docker exec spark-master /opt/spark/bin/spark-submit \
            --master spark://spark-master:7077 \
            --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0 \
            --conf spark.executor.memory=2g \
            --conf spark.driver.memory=1g \
            --conf spark.driver.host=spark-master \
            /opt/spark/apps/crawler/spark/batch_consumer.py
        """,
        env={**os.environ},
    )

    # Task 5: Init Data Warehouse Schema (Idempotent)
    init_dw = BashOperator(
        task_id="init_dw_schema",
        bash_command="python /opt/airflow/scripts/run_sql.py /opt/airflow/dags/sql/init_dw.sql",
        env={**os.environ},
    )

    # Task 6: Transform Unified Jobs to Star Schema
    transform_dw = BashOperator(
        task_id="transform_to_star_schema",
        bash_command="python /opt/airflow/scripts/run_sql.py /opt/airflow/dags/sql/transform_dw.sql",
        env={**os.environ},
    )

    end_task = EmptyOperator(task_id="end")

    # Flow: Crawl -> Producer -> Create Tables -> Spark Consumer -> Init DW -> Transform
    start_task >> crawl_data >> produce_kafka >> create_unified_jobs >> spark_consumer >> init_dw >> transform_dw >> end_task
