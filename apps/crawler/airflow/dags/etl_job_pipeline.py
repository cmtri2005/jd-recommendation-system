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
    description="ETL Pipeline for Job Data (Crawl -> Enrich -> Kafka)",
    schedule_interval="@daily",
    catchup=False,
) as dag:

    start_task = EmptyOperator(task_id="start")

    # Task 1: Produce to Kafka
    produce_kafka = BashOperator(
        task_id="produce_to_kafka",
        bash_command="python /opt/airflow/apps/crawler/kafka/producer.py",
        env={**os.environ, "PYTHONPATH": "/opt/airflow/apps"},
    )

    # Task 2: Init Data Warehouse Schema (Idempotent)
    init_dw = BashOperator(
        task_id="init_dw_schema",
        bash_command="python /opt/airflow/apps/crawler/airflow/scripts/run_sql.py /opt/airflow/apps/crawler/airflow/dags/sql/init_dw.sql",
        env={**os.environ},
    )

    # Task 3: Transform Unfied Jobs to Star Schema
    transform_dw = BashOperator(
        task_id="transform_to_star_schema",
        bash_command="python /opt/airflow/apps/crawler/airflow/scripts/run_sql.py /opt/airflow/apps/crawler/airflow/dags/sql/transform_dw.sql",
        env={**os.environ},
    )

    end_task = EmptyOperator(task_id="end")

    # Flow
    # Crawling & Enrichment are done manually on host.
    # Airflow simply Picks up data -> Kafka -> Spark -> DW.
    start_task >> produce_kafka >> init_dw >> transform_dw >> end_task
