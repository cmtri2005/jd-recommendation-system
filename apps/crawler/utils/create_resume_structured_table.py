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


    create_resume_table_query = """
        CREATE TABLE IF NOT EXISTS resume_structured (
            resume_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            file_path TEXT,
            profile_summary TEXT,
            hard_skills TEXT[],
            soft_skills TEXT[],
            educations TEXT[],
            years_of_experience INTEGER DEFAULT 0,
            certifications TEXT[],
            projects TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    

    create_experiences_table_query = """
        CREATE TABLE IF NOT EXISTS resume_experiences (
            experience_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            resume_id UUID REFERENCES resume_structured(resume_id) ON DELETE CASCADE,
            job_title TEXT,
            company TEXT,
            employment_period TEXT,
            responsibilities TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """
    

    create_indexes_query = """
        CREATE INDEX IF NOT EXISTS idx_resume_experiences_resume_id ON resume_experiences(resume_id);
        CREATE INDEX IF NOT EXISTS idx_resume_structured_created_at ON resume_structured(created_at);
    """
    
    try:
        pc.execute_query(create_resume_table_query)
        pc.execute_query(create_experiences_table_query)
        pc.execute_query(create_indexes_query)
        print("Successfully created resume_structured and resume_experiences tables with indexes")
    except Exception as e:
        print(f"Failed to create tables with error: {e}")


if __name__ == "__main__":
    main()


