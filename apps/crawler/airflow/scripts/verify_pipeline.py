"""
Script to verify Airflow pipeline execution results
Checks data in all tables and provides summary report
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

# Try to load .env file - check multiple locations
env_paths = [
    "/opt/airflow/.env",  # Inside Docker container
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), ".env"),  # Project root
    ".env",  # Current directory
]
for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(env_path)
        break


def get_db_connection(host=None, port=None):
    """
    Get database connection
    Auto-detects if running inside Docker container or outside
    """
    # Default values
    if host is None:
        # Check if running inside Docker container
        if os.path.exists("/opt/airflow/.env") or os.getenv("AIRFLOW_HOME"):
            host = "postgres"  # Docker network hostname
        else:
            host = "localhost"  # Outside container
    
    if port is None:
        port = os.getenv("POSTGRES_PORT", "5432")
    
    dbname = os.getenv("POSTGRES_DB", "airflow")
    user = os.getenv("POSTGRES_USER", "airflow")
    password = os.getenv("POSTGRES_PASSWORD", "airflow")
    
    # Allow command-line override
    if "--host" in sys.argv:
        idx = sys.argv.index("--host")
        if idx + 1 < len(sys.argv):
            host = sys.argv[idx + 1]
    
    if "--port" in sys.argv:
        idx = sys.argv.index("--port")
        if idx + 1 < len(sys.argv):
            port = sys.argv[idx + 1]

    conn_str = (
        f"host={host} port={port} dbname={dbname} user={user} password={password}"
    )
    
    print(f"Connecting to PostgreSQL at {host}:{port}...")
    return psycopg2.connect(conn_str)


def check_table_exists(conn, table_name):
    """Check if table exists"""
    cur = conn.cursor()
    cur.execute("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = %s
        );
    """, (table_name,))
    exists = cur.fetchone()[0]
    cur.close()
    return exists


def get_table_count(conn, table_name):
    """Get record count from table"""
    if not check_table_exists(conn, table_name):
        return None
    
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT COUNT(*) FROM {table_name};")
        count = cur.fetchone()[0]
        return count
    except Exception as e:
        return f"Error: {e}"
    finally:
        cur.close()


def get_sample_data(conn, table_name, limit=5):
    """Get sample data from table"""
    if not check_table_exists(conn, table_name):
        return []
    
    cur = conn.cursor()
    try:
        cur.execute(f"SELECT * FROM {table_name} LIMIT {limit};")
        columns = [desc[0] for desc in cur.description]
        rows = cur.fetchall()
        
        result = []
        for row in rows:
            result.append(dict(zip(columns, row)))
        return result
    except Exception as e:
        return [f"Error: {e}"]
    finally:
        cur.close()


def verify_pipeline(host=None, port=None):
    """Verify pipeline execution results"""
    print("=" * 70)
    print("AIRFLOW PIPELINE VERIFICATION REPORT")
    print("=" * 70)
    print()
    
    conn = get_db_connection(host=host, port=port)
    
    try:
        # 1. Check unified_jobs table
        print("📊 1. UNIFIED_JOBS TABLE (Staging)")
        print("-" * 70)
        unified_count = get_table_count(conn, "unified_jobs")
        if unified_count is not None:
            print(f"   ✅ Table exists")
            print(f"   📈 Total records: {unified_count}")
            
            if unified_count > 0:
                # Get sample
                sample = get_sample_data(conn, "unified_jobs", 3)
                if sample:
                    print(f"   📝 Sample records:")
                    for i, record in enumerate(sample[:2], 1):
                        print(f"      {i}. {record.get('job_title', 'N/A')} - {record.get('company_name', 'N/A')}")
        else:
            print(f"   ❌ Table does not exist")
        print()
        
        # 2. Check Dimension Tables
        print("📊 2. DIMENSION TABLES")
        print("-" * 70)
        dimensions = {
            "dim_company": "Companies",
            "dim_location": "Locations",
            "dim_skill": "Skills",
            "dim_date": "Dates"
        }
        
        for table, name in dimensions.items():
            count = get_table_count(conn, table)
            if count is not None:
                status = "✅" if count > 0 else "⚠️"
                print(f"   {status} {name:20} ({table:20}): {count} records")
            else:
                print(f"   ❌ {name:20} ({table:20}): Table not found")
        print()
        
        # 3. Check Fact Tables
        print("📊 3. FACT TABLES")
        print("-" * 70)
        facts = {
            "fact_job_postings": "Job Postings",
            "fact_job_skills": "Job-Skill Relationships"
        }
        
        for table, name in facts.items():
            count = get_table_count(conn, table)
            if count is not None:
                status = "✅" if count > 0 else "⚠️"
                print(f"   {status} {name:30} ({table:25}): {count} records")
            else:
                print(f"   ❌ {name:30} ({table:25}): Table not found")
        print()
        
        # 4. Data Quality Checks
        print("📊 4. DATA QUALITY CHECKS")
        print("-" * 70)
        
        # Check if fact_job_postings has foreign keys
        if check_table_exists(conn, "fact_job_postings"):
            cur = conn.cursor()
            
            # Check jobs with company
            cur.execute("""
                SELECT COUNT(*) FROM fact_job_postings 
                WHERE company_id IS NOT NULL;
            """)
            jobs_with_company = cur.fetchone()[0]
            
            # Check jobs with location
            cur.execute("""
                SELECT COUNT(*) FROM fact_job_postings 
                WHERE location_id IS NOT NULL;
            """)
            jobs_with_location = cur.fetchone()[0]
            
            # Check jobs with skills
            cur.execute("""
                SELECT COUNT(DISTINCT job_id) FROM fact_job_skills;
            """)
            jobs_with_skills = cur.fetchone()[0]
            
            total_jobs = get_table_count(conn, "fact_job_postings")
            
            print(f"   📌 Jobs with company mapping: {jobs_with_company}/{total_jobs}")
            print(f"   📌 Jobs with location mapping: {jobs_with_location}/{total_jobs}")
            print(f"   📌 Jobs with skills: {jobs_with_skills}/{total_jobs}")
            
            cur.close()
        print()
        
        # 5. Summary Statistics
        print("📊 5. SUMMARY STATISTICS")
        print("-" * 70)
        
        if check_table_exists(conn, "fact_job_postings"):
            cur = conn.cursor()
            
            # Top companies
            cur.execute("""
                SELECT dc.company_name, COUNT(*) as job_count
                FROM fact_job_postings fjp
                JOIN dim_company dc ON fjp.company_id = dc.company_id
                GROUP BY dc.company_id, dc.company_name
                ORDER BY job_count DESC
                LIMIT 5;
            """)
            top_companies = cur.fetchall()
            
            if top_companies:
                print("   🏢 Top 5 Companies by Job Count:")
                for company, count in top_companies:
                    print(f"      - {company}: {count} jobs")
            
            # Top locations
            cur.execute("""
                SELECT dl.city_name, COUNT(*) as job_count
                FROM fact_job_postings fjp
                JOIN dim_location dl ON fjp.location_id = dl.location_id
                GROUP BY dl.location_id, dl.city_name
                ORDER BY job_count DESC
                LIMIT 5;
            """)
            top_locations = cur.fetchall()
            
            if top_locations:
                print("   📍 Top 5 Locations by Job Count:")
                for location, count in top_locations:
                    print(f"      - {location}: {count} jobs")
            
            # Top skills
            cur.execute("""
                SELECT ds.skill_name, COUNT(*) as job_count
                FROM fact_job_skills fjs
                JOIN dim_skill ds ON fjs.skill_id = ds.skill_id
                GROUP BY ds.skill_id, ds.skill_name
                ORDER BY job_count DESC
                LIMIT 10;
            """)
            top_skills = cur.fetchall()
            
            if top_skills:
                print("   💻 Top 10 Skills by Job Count:")
                for skill, count in top_skills:
                    print(f"      - {skill}: {count} jobs")
            
            cur.close()
        print()
        
        # 6. Pipeline Status
        print("📊 6. PIPELINE STATUS")
        print("-" * 70)
        
        unified_count = get_table_count(conn, "unified_jobs")
        fact_count = get_table_count(conn, "fact_job_postings")
        company_count = get_table_count(conn, "dim_company")
        location_count = get_table_count(conn, "dim_location")
        skill_count = get_table_count(conn, "dim_skill")
        
        all_good = (
            unified_count and unified_count > 0 and
            fact_count and fact_count > 0 and
            company_count and company_count > 0 and
            location_count and location_count > 0 and
            skill_count and skill_count > 0
        )
        
        if all_good:
            print("   ✅ Pipeline execution: SUCCESS")
            print("   ✅ All tables populated with data")
            print("   ✅ Star Schema transformation: COMPLETE")
        else:
            print("   ⚠️  Pipeline execution: PARTIAL")
            if not unified_count or unified_count == 0:
                print("   ⚠️  unified_jobs table is empty")
            if not fact_count or fact_count == 0:
                print("   ⚠️  fact_job_postings table is empty")
        
        print()
        print("=" * 70)
        
    except Exception as e:
        print(f"❌ Error during verification: {e}")
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Verify Airflow pipeline execution results",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run inside Docker container (default)
  docker exec airflow-webserver python /opt/airflow/scripts/verify_pipeline.py
  
  # Run outside Docker container (auto-detects localhost)
  python apps/crawler/airflow/scripts/verify_pipeline.py
  
  # Override host and port
  python apps/crawler/airflow/scripts/verify_pipeline.py --host localhost --port 5432
        """
    )
    parser.add_argument("--host", type=str, help="PostgreSQL host (default: auto-detect)")
    parser.add_argument("--port", type=str, help="PostgreSQL port (default: 5432)")
    
    args = parser.parse_args()
    
    try:
        verify_pipeline(host=args.host, port=args.port)
    except psycopg2.OperationalError as e:
        print(f"\n❌ Connection Error: {e}")
        print("\n💡 Tips:")
        print("  - If running outside Docker, make sure PostgreSQL is accessible on localhost:5432")
        print("  - Or use: python verify_pipeline.py --host localhost --port 5432")
        print("  - Or run inside Docker: docker exec airflow-webserver python /opt/airflow/scripts/verify_pipeline.py")
        sys.exit(1)

