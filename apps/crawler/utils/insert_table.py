import os
from datetime import date
from time import sleep
from typing import List

from dotenv import load_dotenv
from utils.postgresql_client import PostgreSQLClient

load_dotenv()

TABLE_NAME = "jd_rcm"
NUM_ROWS = 1000


def insert_table(
    type_job: str, required_skills: List[str], posted_date: date, url: str
):
    pc = PostgreSQLClient(
        database=os.getenv("POSTGRES_DB"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
    )
    parameters = (type_job,required_skills,posted_date,url)
    query = f"""
        insert into {TABLE_NAME} (type_job,required_skills,posted_date,url)
        values (%s,%s,%s,%s)
        ON CONFLICT (url) DO NOTHING
    """
    pc.execute_query(query, parameters)
    sleep(2)


if __name__ == "__main__":
    insert_table()
