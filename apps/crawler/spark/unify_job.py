from pyspark.sql import SparkSession
from pyspark.sql.functions import (
    col,
    from_json,
    current_timestamp,
    lit,
    concat_ws,
    split,
    array,
    when,
    coalesce,
    to_json,
    struct,
    sha2,
    current_date,
)
from pyspark.sql.types import (
    StructType,
    StructField,
    StringType,
    ArrayType,
    BooleanType,
    FloatType,
)


def create_spark_session():
    return (
        SparkSession.builder.appName("JobUnification")
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
            # New enriched fields
            StructField("normalized_level", StringType(), True),
            StructField("normalized_exp_years", FloatType(), True),
            StructField("normalized_skills", ArrayType(StringType()), True),
        ]
    )


def write_to_postgres(df, batch_id):
    print(f"Processing Batch ID: {batch_id} - Count: {df.count()}")
    try:
        df.write.format("jdbc").option(
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
    except Exception as e:
        print(f"Error writing to Postgres: {e}")


def main():
    spark = create_spark_session()
    spark.sparkContext.setLogLevel("WARN")

    # --- TopCV Stream ---
    df_topcv_raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", "kafka:29092")
        .option("subscribe", "raw_topcv")
        .option("startingOffsets", "earliest")
        .load()
    )

    df_topcv_parsed = df_topcv_raw.select(
        from_json(col("value").cast("string"), get_topcv_schema()).alias("data")
    ).select("data.*")

    # --- Transformation Logic based on User's Unified Schema ---

    # Logic to hash URL for job_id (using sha2 function if available or similar)

    # --- TopCV Transformation ---
    df_topcv_unified = df_topcv_parsed.select(
        sha2(col("url"), 256).alias("job_id"),
        lit("TopCV").alias("source"),
        col("url"),
        # Company Attributes
        col("company_name"),
        col("company_industry"),
        col("company_scale").alias("company_size"),  # Mapping from user
        col("company_url"),
        # Job Attributes
        col("job_title"),
        col("job_description"),
        col("job_requirements"),
        col(
            "job_benefits"
        ),  # TopCV benefits is often a string with \n or list? Schema said string in analysis but lets keep raw.
        col("salary"),
        col("job_level"),
        lit(None)
        .cast(FloatType())
        .alias(
            "experience_years"
        ),  # TopCV raw doesn't strictly parse this yet without LLM
        # Skills & Location
        col("tags_skill").alias("skills"),  # Array
        col("province").alias("location_city"),
        col("job_type").alias("work_model"),  # Map job_type to work_model
    )

    # --- ITViec Stream ---
    df_itviec_raw = (
        spark.readStream.format("kafka")
        .option("kafka.bootstrap.servers", "kafka:29092")
        .option("subscribe", "raw_itviec")
        .option("startingOffsets", "earliest")
        .load()
    )

    df_itviec_parsed = df_itviec_raw.select(
        from_json(col("value").cast("string"), get_itviec_schema()).alias("data")
    ).select("data.*")

    # --- ITViec Transformation ---
    # Using Enriched Fields for level and experience
    df_itviec_unified = df_itviec_parsed.select(
        sha2(col("url"), 256).alias("job_id"),
        lit("ITViec").alias("source"),
        col("url"),
        # Company Attributes
        col("company_name"),
        col("company_industry"),
        col("company_size"),
        col("company_url"),
        # Job Attributes
        col("job_title"),
        col("job_description"),
        col("your_skills_experience").alias("job_requirements"),
        concat_ws("\n", col("employment_benefits")).alias("job_benefits"),
        lit("N/A").alias("salary"),
        col("normalized_level").alias("job_level"),  # From LLM
        col("normalized_exp_years").alias("experience_years"),  # From LLM
        # Skills & Location
        coalesce(col("normalized_skills"), col("required_skills")).alias("skills"),
        # Location
        coalesce(
            when(col("address").contains("Ho Chi Minh"), "Ho Chi Minh")
            .when(col("address").contains("Ha Noi"), "Ha Noi")
            .when(col("address").contains("Da Nang"), "Da Nang")
            .otherwise(col("address"))
        ).alias("location_city"),
        # Work Model
        col("work_model"),  # Use the direct work_model field
    )

    # Union
    df_unified = df_topcv_unified.unionByName(df_itviec_unified)

    # Write Stream
    query = (
        df_unified.writeStream.foreachBatch(write_to_postgres)
        .option("checkpointLocation", "/tmp/spark-checkpoint-unified")
        .outputMode("update")
        .trigger(processingTime="10 seconds")
        .start()
    )

    query.awaitTermination()


if __name__ == "__main__":
    main()
