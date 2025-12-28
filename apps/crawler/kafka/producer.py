import json
import os
import time
from kafka import KafkaProducer, KafkaAdminClient
from kafka.admin import NewTopic
from kafka.errors import TopicAlreadyExistsError


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_jsonl(path):
    data = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    data.append(json.loads(line))
                except:
                    pass
    return data


def create_topics():
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    try:
        admin_client = KafkaAdminClient(
            bootstrap_servers=[bootstrap_servers], client_id="job_data_admin"
        )

        topic_list = []
        topic_list.append(
            NewTopic(name="raw_topcv", num_partitions=1, replication_factor=1)
        )
        topic_list.append(
            NewTopic(name="raw_itviec", num_partitions=1, replication_factor=1)
        )

        print(f"Creating topics on {bootstrap_servers}...")
        admin_client.create_topics(new_topics=topic_list, validate_only=False)
        print("Topics created successfully.")
    except TopicAlreadyExistsError:
        print("Topics already exist.")
    except Exception as e:
        print(f"Error creating topics: {e}")
    finally:
        try:
            admin_client.close()
        except:
            pass


def create_producer():
    bootstrap_servers = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")
    # Retry connection logic
    retries = 5
    while retries > 0:
        try:
            producer = KafkaProducer(
                bootstrap_servers=[bootstrap_servers],
                value_serializer=lambda x: json.dumps(x).encode("utf-8"),
            )
            print(f"Connected to Kafka at {bootstrap_servers} successfully.")
            return producer
        except Exception as e:
            print(f"Failed to connect to Kafka: {e}. Retrying in 5 seconds...")
            time.sleep(5)
            retries -= 1
    raise Exception("Could not connect to Kafka after multiple retries.")


def main():
    base_dir = os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    )
    topcv_path = os.path.join(
        base_dir, "crawler", "data", "raw_topcv", "job_details.json"
    )

    # Prefer enriched data for ITViec, fallback to raw
    itviec_enriched_path = os.path.join(
        base_dir, "crawler", "data", "raw_itviec", "itviec_enriched.jsonl"
    )
    itviec_raw_path = os.path.join(
        base_dir, "crawler", "data", "raw_itviec", "jobs_details_cleaned.jsonl"
    )

    itviec_path = (
        itviec_enriched_path
        if os.path.exists(itviec_enriched_path)
        else itviec_raw_path
    )

    # Checkpoint file path
    checkpoint_file = os.path.join(base_dir, "crawler", "kafka", "processed_urls.txt")
    processed_urls = set()
    if os.path.exists(checkpoint_file):
        with open(checkpoint_file, "r", encoding="utf-8") as f:
            processed_urls = set(line.strip() for line in f)

    # 1. Create Topics explicitly
    create_topics()

    # 2. Start Producer
    producer = create_producer()

    new_urls = []

    # Publish TopCV Data
    if os.path.exists(topcv_path):
        print(f"Reading TopCV file from {topcv_path}...")
        topcv_raw = load_json(topcv_path)
        topcv_list = []
        if isinstance(topcv_raw, dict) and "jobs" in topcv_raw:
            topcv_list = topcv_raw["jobs"]
        elif isinstance(topcv_raw, list):
            topcv_list = topcv_raw

        # Filter new
        topcv_to_send = [
            job for job in topcv_list if job.get("url") not in processed_urls
        ]

        print(
            f"Sending {len(topcv_to_send)} NEW records (out of {len(topcv_list)}) to 'raw_topcv'..."
        )
        for item in topcv_to_send:
            producer.send("raw_topcv", value=item)
            if item.get("url"):
                new_urls.append(item["url"])

        producer.flush()
        print("Finished sending TopCV data.")
    else:
        print(f"TopCV file not found at {topcv_path}")

    # Publish ITViec Data
    if os.path.exists(itviec_path):
        print(f"Reading ITViec file from {itviec_path}...")
        itviec_list = load_jsonl(itviec_path)

        # Filter new
        itviec_to_send = [
            job for job in itviec_list if job.get("url") not in processed_urls
        ]

        print(
            f"Sending {len(itviec_to_send)} NEW records (out of {len(itviec_list)}) to 'raw_itviec'..."
        )
        for item in itviec_to_send:
            producer.send("raw_itviec", value=item)
            if item.get("url"):
                new_urls.append(item["url"])

        producer.flush()
        print("Finished sending ITViec data.")
    else:
        print(f"ITViec file not found at {itviec_path} (checked enriched and raw)")

    producer.close()

    # Save checkpoint
    if new_urls:
        with open(checkpoint_file, "a", encoding="utf-8") as f:
            for url in new_urls:
                f.write(url + "\n")
        print(f"Updated checkpoint with {len(new_urls)} new URLs.")


if __name__ == "__main__":
    main()
