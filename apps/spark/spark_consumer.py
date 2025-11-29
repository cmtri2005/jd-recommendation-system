import logging
from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, concat_ws
from pyspark.sql.types import StructType, StringType, ArrayType

schema = StructType() \
    .add("url", StringType()) \
    .add("job_title", StringType()) \
    .add("required_skills", ArrayType(StringType())) \
    .add("time_posted_raw", StringType()) \
    .add("job_description", StringType()) \
    .add("your_skills_experience", StringType()) 

def write_to_postgres(batch_df, batch_id):
    # Cache lại dataframe vì chúng ta sẽ dùng nó 2 lần (count và write)
    batch_df.persist()
    
    count = batch_df.count()
    print(f"--> Dang xu ly Batch ID: {batch_id} | So luong: {count}")
    
    if count > 0:
        try:
            (batch_df.write
                .format("jdbc")
                .option("url", "jdbc:postgresql://postgres:5432/airflow")
                .option("driver", "org.postgresql.Driver")
                .option("dbtable", "job_raw")
                .option("user", "airflow")
                .option("password", "airflow")
                .mode("append")
                .save())
        except Exception as e:
            print(f"!!! Loi ghi vao DB (co the do trung lap): {e}")
            
    batch_df.unpersist()

def main():
    spark = SparkSession.builder \
        .appName("JobConsumer") \
        .config("spark.sql.streaming.checkpointLocation", "/tmp/spark-checkpoint") \
        .getOrCreate()

    spark.sparkContext.setLogLevel("WARN")

    # 1. Đọc từ Kafka
    df = spark.readStream \
        .format("kafka") \
        .option("kafka.bootstrap.servers", "kafka:29092") \
        .option("subscribe", "job_topic") \
        .option("startingOffsets", "earliest") \
        .load()

    # 2. Parse JSON
    json_df = df.select(from_json(col("value").cast("string"), schema).alias("data")).select("data.*")
    
    # 3. Xử lý dữ liệu
    processed_df = json_df \
        .withColumn("required_skills", concat_ws(", ", col("required_skills"))) \
        .dropDuplicates(["url"])  

    # 4. Ghi xuống DB
    # Thêm checkpointLocation để Spark nhớ nó đã đọc đến đâu
    query = processed_df.writeStream \
        .foreachBatch(write_to_postgres) \
        .option("checkpointLocation", "/tmp/spark-checkpoint") \
        .outputMode("update") \
        .start()

    query.awaitTermination()

if __name__ == "__main__":
    main()