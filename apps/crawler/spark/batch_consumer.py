"""
Spark Batch Consumer - Consume từ Kafka và ghi vào PostgreSQL
Chạy batch mode (không streaming) - đọc tất cả messages và dừng
"""
from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    from_json,
    lit,
    concat_ws,
    coalesce,
    when,
    sha2,
)
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    ArrayType,
    FloatType,
)


def create_spark_session():
    return (
        SparkSession.builder.appName("JobUnificationBatch")
        .config(
            "spark.jars.packages",
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0",
        )
        .getOrCreate()
    )


def get_topcv_schema():
    return StructType(
        [
            StructField("url", StringType(), True),
            StructField("job_title", StringType(), True),
            StructField("company_name", StringType(), True),
            StructField("company_url", StringType(), True),
            StructField("company_industry", StringType(), True),
            StructField("company_scale", StringType(), True),
            StructField("company_address", StringType(), True),
            StructField("job_description", StringType(), True),
            StructField("job_requirements", StringType(), True),
            StructField("job_benefits", StringType(), True),
            StructField("salary", StringType(), True),
            StructField("job_level", StringType(), True),
            StructField("job_type", StringType(), True),
            StructField("quantity", StringType(), True),
            StructField("deadline", StringType(), True),
            StructField("crawled_at", StringType(), True),
            StructField("job_location_detail", StringType(), True),
            StructField("province", StringType(), True),
            StructField("tags_skill", ArrayType(StringType()), True),
            StructField("tags_role", ArrayType(StringType()), True),
        ]
    )


def get_itviec_schema():
    return StructType(
        [
            StructField("url", StringType(), True),
            StructField("job_title", StringType(), True),
            StructField("company_name", StringType(), True),
            StructField("company_url", StringType(), True),
            StructField("company_industry", StringType(), True),
            StructField("company_size", StringType(), True),
            StructField("address", StringType(), True),
            StructField("job_description", StringType(), True),
            StructField("your_skills_experience", StringType(), True),
            StructField("employment_benefits", ArrayType(StringType()), True),
            StructField("work_model", StringType(), True),
            StructField("working_days", StringType(), True),
            StructField("time_posted_raw", StringType(), True),
            StructField("required_skills", ArrayType(StringType()), True),
            StructField("country", StringType(), True),
            StructField("normalized_level", StringType(), True),
            StructField("normalized_exp_years", FloatType(), True),
            StructField("normalized_skills", ArrayType(StringType()), True),
        ]
    )


def main():
    
    from pyspark.sql.functions import col, from_json, lit, concat_ws, coalesce, when, sha2
    
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    kafka_bootstrap = "kafka:29092"
    print(f"Connecting to Kafka at {kafka_bootstrap}...")

    # --- Read TopCV from Kafka (BATCH MODE) ---
    print("Reading TopCV data from Kafka...")
    try:
        df_topcv_raw = (
            spark.read.format("kafka")
            .option("kafka.bootstrap.servers", kafka_bootstrap)
            .option("subscribe", "raw_topcv")
            .option("startingOffsets", "earliest")
            .option("endingOffsets", "latest")
            .load()
        )

        if df_topcv_raw.count() > 0:
            print(f"Found {df_topcv_raw.count()} TopCV messages")
            df_topcv_parsed = df_topcv_raw.select(
                from_json(col("value").cast("string"), get_topcv_schema()).alias("data")
            ).select("data.*")

            df_topcv_unified = df_topcv_parsed.select(
                sha2(col("url"), 256).alias("job_id"),
                lit("TopCV").alias("source"),
                col("url"),
                col("company_name"),
                col("company_industry"),
                col("company_scale").alias("company_size"),
                col("company_url"),
                col("job_title"),
                col("job_description"),
                col("job_requirements"),
                col("job_benefits"),
                col("salary"),
                col("job_level"),
                lit(None).cast(FloatType()).alias("experience_years"),
                col("tags_skill").alias("skills"),
                col("province").alias("location_city"),
                col("job_type").alias("work_model"),
            )
        else:
            print("No TopCV messages found")
            df_topcv_unified = None
    except Exception as e:
        print(f"Error reading TopCV: {e}")
        df_topcv_unified = None

    # --- Read ITViec from Kafka (BATCH MODE) ---
    print("Reading ITViec data from Kafka...")
    try:
        df_itviec_raw = (
            spark.read.format("kafka")
            .option("kafka.bootstrap.servers", kafka_bootstrap)
            .option("subscribe", "raw_itviec")
            .option("startingOffsets", "earliest")
            .option("endingOffsets", "latest")
            .load()
        )

        if df_itviec_raw.count() > 0:
            print(f"Found {df_itviec_raw.count()} ITViec messages")
            df_itviec_parsed = df_itviec_raw.select(
                from_json(col("value").cast("string"), get_itviec_schema()).alias("data")
            ).select("data.*")

            df_itviec_unified = df_itviec_parsed.select(
                sha2(col("url"), 256).alias("job_id"),
                lit("ITViec").alias("source"),
                col("url"),
                col("company_name"),
                col("company_industry"),
                col("company_size"),
                col("company_url"),
                col("job_title"),
                col("job_description"),
                col("your_skills_experience").alias("job_requirements"),
                concat_ws("\n", col("employment_benefits")).alias("job_benefits"),
                lit("N/A").alias("salary"),
                col("normalized_level").alias("job_level"),
                col("normalized_exp_years").alias("experience_years"),
                coalesce(col("normalized_skills"), col("required_skills")).alias("skills"),
                coalesce(
                    when(col("address").contains("Ho Chi Minh"), "Ho Chi Minh")
                    .when(col("address").contains("Ha Noi"), "Ha Noi")
                    .when(col("address").contains("Da Nang"), "Da Nang")
                    .otherwise(col("address"))
                ).alias("location_city"),
                col("work_model"),
            )
        else:
            print("No ITViec messages found")
            df_itviec_unified = None
    except Exception as e:
        print(f"Error reading ITViec: {e}")
        df_itviec_unified = None

    # --- Union và Write to PostgreSQL ---
    if df_topcv_unified is not None and df_itviec_unified is not None:
        df_unified = df_topcv_unified.unionByName(df_itviec_unified)
    elif df_topcv_unified is not None:
        df_unified = df_topcv_unified
    elif df_itviec_unified is not None:
        df_unified = df_itviec_unified
    else:
        print("No data to process. Exiting.")
        spark.stop()
        return

    # Remove duplicates within the batch first
    df_unified = df_unified.dropDuplicates(["job_id"])
    count = df_unified.count()
    print(f"Total unified records (after removing duplicates in batch): {count}")

    if count > 0:
        # Filter out existing records using left anti join (more efficient than collect)
        print("Checking for existing records in database...")
        try:
            # Read existing job_ids from database
            df_existing = spark.read.format("jdbc").option(
                "url", "jdbc:postgresql://postgres:5432/airflow"
            ).option("driver", "org.postgresql.Driver").option(
                "dbtable", "(SELECT job_id FROM unified_jobs) AS existing"
            ).option(
                "user", "airflow"
            ).option(
                "password", "airflow"
            ).load()
            
            # Use left anti join to filter out existing records
            df_new = df_unified.join(df_existing, "job_id", "left_anti")
            new_count = df_new.count()
            print(f"After filtering duplicates: {new_count} new records to insert")
            
            if new_count > 0:
                print("Writing new records to PostgreSQL...")
                df_new.write.format("jdbc").option(
                    "url", "jdbc:postgresql://postgres:5432/airflow"
                ).option("driver", "org.postgresql.Driver").option(
                    "dbtable", "unified_jobs"
                ).option(
                    "user", "airflow"
                ).option(
                    "password", "airflow"
                ).mode(
                    "append"
                ).save()
                print(f"Successfully wrote {new_count} new records to unified_jobs table")
            else:
                print("No new records to insert (all records already exist)")
        except Exception as e:
            error_msg = str(e)
            # Check if error is due to duplicates (race condition)
            if "duplicate key" in error_msg.lower() or "unique constraint" in error_msg.lower():
                print(f"⚠️  Warning: Some duplicates detected (possible race condition): {error_msg}")
                print("This is expected if pipeline runs concurrently. Records were filtered but some may have been inserted by another process.")
                print("Pipeline will continue - duplicates are handled by database constraints.")
            else:
                print(f"❌ Error writing to Postgres: {e}")
                raise
    else:
        print("No records to write")

    spark.stop()
    print("Batch consumer completed.")


if __name__ == "__main__":
    main()

