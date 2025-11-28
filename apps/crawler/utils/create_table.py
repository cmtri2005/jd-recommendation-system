import os

from dotenv import load_dotenv
from utils.postgresql_client import PostgreSQLClient

load_dotenv()


def main():
    pc = PostgreSQLClient(
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )

    pc.execute_query('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    create_table_query = """
        CREATE TABLE IF NOT EXISTS jd_rcm(
            jd_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            type_job TEXT,
            required_skills TEXT[],
            posted_date DATE,
            url TEXT UNIQUE
        )
    """
    try:
        pc.execute_query(create_table_query)
    except Exception as e:
        print(f"Failed to create table with error: {e}")


if __name__ == "__main__":
    main()
