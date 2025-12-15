import os
from dotenv import load_dotenv
from utils.postgresql_client import PostgreSQLClient


load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env'))


def main():
    pc = PostgreSQLClient(
        database=os.getenv("POSTGRES_DB", "airflow"),
        user=os.getenv("POSTGRES_USER", "airflow"),
        password=os.getenv("POSTGRES_PASSWORD", "airflow"),
        host=os.getenv("POSTGRES_HOST", "localhost"),
        port=int(os.getenv("POSTGRES_PORT", 5432))
    )

    
    pc.execute_query('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    create_table_query = """
        CREATE TABLE IF NOT EXISTS jd_structured (
            jd_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            url TEXT UNIQUE,
            job_summary TEXT,
            require_hard_skills TEXT[],
            optional_hard_skills TEXT[],
            required_soft_skills TEXT[],
            optional_soft_skills TEXT[],
            required_work_experiences TEXT[],
            optional_work_experiences TEXT[],
            required_educations TEXT[],
            optional_educations TEXT[],
            required_years_of_experience INTEGER DEFAULT 0,
            posted_date DATE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    
    
    create_index_query = """
        CREATE INDEX IF NOT EXISTS idx_jd_structured_url ON jd_structured(url);
        CREATE INDEX IF NOT EXISTS idx_jd_structured_created_at ON jd_structured(created_at);
    """
    
    try:
        pc.execute_query(create_table_query)
        pc.execute_query(create_index_query)
        print("Successfully created jd_structured table and indexes")
    except Exception as e:
        print(f"Failed to create table with error: {e}")


if __name__ == "__main__":
    main()


