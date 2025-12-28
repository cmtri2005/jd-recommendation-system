import json
import time
import os
from kafka import KafkaProducer


def json_serializer(data):
    return json.dumps(data).encode("utf-8")


def produce_jobs():
    producer = KafkaProducer(
        bootstrap_servers=["localhost:9092"], value_serializer=json_serializer
    )

    base_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(base_dir, "..", "data", "jobs_raw.jsonl")

    if not os.path.exists(file_path):
        print(f"Lỗi: Không tìm thấy file {file_path}")
        print("Bạn hãy chạy crawl.py trước để lấy dữ liệu nhé!")
        return

    print(f"Bắt đầu đọc file {file_path} và đẩy vào Kafka...")

    topic_name = "job_topic"
    count = 0

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():

                job_data = json.loads(line)

                producer.send(topic_name, job_data)

                count += 1

                print(
                    f"[{count}] Sent to Kafka: {job_data.get('job_title', 'Unknown')}"
                )

                time.sleep(0.05)

    producer.flush()
    print(f"✅ Hoàn tất! Đã gửi {count} jobs vào topic '{topic_name}'.")


if __name__ == "__main__":
    produce_jobs()
