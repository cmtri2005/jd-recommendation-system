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
        CREATE TABLE IF NOT EXISTS matching_results (
            match_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            resume_id UUID REFERENCES resume_structured(resume_id) ON DELETE CASCADE,
            jd_id UUID REFERENCES jd_structured(jd_id) ON DELETE CASCADE,
            total_score REAL,
            document_score REAL,
            experience_score REAL,
            project_score REAL,
            skills_score REAL,
            experience_ratio REAL,
            years_score REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(resume_id, jd_id)
        );
    """
    
  
    create_indexes_query = """
        CREATE INDEX IF NOT EXISTS idx_matching_resume ON matching_results(resume_id);
        CREATE INDEX IF NOT EXISTS idx_matching_jd ON matching_results(jd_id);
        CREATE INDEX IF NOT EXISTS idx_matching_score ON matching_results(total_score DESC);
        CREATE INDEX IF NOT EXISTS idx_matching_created_at ON matching_results(created_at);
    """
    
    try:
        pc.execute_query(create_table_query)
        pc.execute_query(create_indexes_query)
        print("Successfully created matching_results table with indexes")
    except Exception as e:
        print(f"Failed to create table with error: {e}")


if __name__ == "__main__":
    main()


