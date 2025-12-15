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

    # Create UUID extension if not exists
    pc.execute_query('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

    # Create jd_embeddings table
    create_jd_embeddings_query = """
        CREATE TABLE IF NOT EXISTS jd_embeddings (
            embedding_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            jd_id UUID REFERENCES jd_structured(jd_id) ON DELETE CASCADE,
            embedding_type TEXT NOT NULL, -- 'document', 'experience', 'project'
            embedding_vector REAL[], -- Array of floats
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(jd_id, embedding_type)
        );
    """
    
    # Create resume_embeddings table
    create_resume_embeddings_query = """
        CREATE TABLE IF NOT EXISTS resume_embeddings (
            embedding_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            resume_id UUID REFERENCES resume_structured(resume_id) ON DELETE CASCADE,
            embedding_type TEXT NOT NULL, -- 'document', 'experience', 'project'
            embedding_vector REAL[], -- Array of floats
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(resume_id, embedding_type)
        );
    """
    
    # Create indexes for faster queries
    create_indexes_query = """
        CREATE INDEX IF NOT EXISTS idx_jd_embeddings_jd_id ON jd_embeddings(jd_id);
        CREATE INDEX IF NOT EXISTS idx_jd_embeddings_type ON jd_embeddings(embedding_type);
        CREATE INDEX IF NOT EXISTS idx_resume_embeddings_resume_id ON resume_embeddings(resume_id);
        CREATE INDEX IF NOT EXISTS idx_resume_embeddings_type ON resume_embeddings(embedding_type);
    """
    
    try:
        pc.execute_query(create_jd_embeddings_query)
        pc.execute_query(create_resume_embeddings_query)
        pc.execute_query(create_indexes_query)
        print("Successfully created jd_embeddings and resume_embeddings tables with indexes")
    except Exception as e:
        print(f"Failed to create tables with error: {e}")


if __name__ == "__main__":
    main()


