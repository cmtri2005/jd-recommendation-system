import os
import argparse
import psycopg2
from dotenv import load_dotenv

load_dotenv("/opt/airflow/.env")


def get_db_connection():
    host = "postgres"
    port = "5432"
    dbname = os.getenv("POSTGRES_DB", "airflow")
    user = os.getenv("POSTGRES_USER", "airflow")
    password = os.getenv("POSTGRES_PASSWORD", "airflow")

    conn_str = (
        f"host={host} port={port} dbname={dbname} user={user} password={password}"
    )
    return psycopg2.connect(conn_str)


def run_sql_file(file_path):
    print(f"Executing SQL file: {file_path}")
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        with open(file_path, "r", encoding="utf-8") as f:
            sql_commands = f.read()

        cur.execute(sql_commands)
        conn.commit()
        print("Success.")
        cur.close()
    except Exception as e:
        print(f"Error executing SQL: {e}")
        conn.rollback()
        raise e
    finally:
        conn.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Execute SQL file against Postgres")
    parser.add_argument("file_path", type=str, help="Absolute path to SQL file")

    args = parser.parse_args()
    run_sql_file(args.file_path)
