"""
Script để xóa data trong database (fresh start)
Chạy script này nếu muốn reset toàn bộ data và chạy lại pipeline từ đầu
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv


load_dotenv("/opt/airflow/.env")

def get_db_connection():
    """Get PostgreSQL connection"""
    conn_str = os.getenv(
        "AIRFLOW__DATABASE__SQL_ALCHEMY_CONN",
        "postgresql://airflow:airflow@postgres:5432/airflow"
    )

    if "postgresql://" in conn_str:
        conn_str = conn_str.replace("postgresql://", "")
        parts = conn_str.split("@")
        user_pass = parts[0].split(":")
        host_port_db = parts[1].split("/")
        host_port = host_port_db[0].split(":")
        
        user = user_pass[0]
        password = user_pass[1] if len(user_pass) > 1 else "airflow"
        host = host_port[0]
        port = host_port[1] if len(host_port) > 1 else "5432"
        database = host_port_db[1] if len(host_port_db) > 1 else "airflow"
    else:
        # Fallback to defaults
        user = "airflow"
        password = "airflow"
        host = "postgres"
        port = "5432"
        database = "airflow"
    
    return psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )

def clear_data():
    """Clear all data from fact and dimension tables, keep unified_jobs"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("=" * 60)
        print("CLEARING DATA FROM DATA WAREHOUSE")
        print("=" * 60)
        
        # Clear fact tables first (due to foreign keys)
        print("\n1. Clearing fact_job_skills...")
        cursor.execute("DELETE FROM fact_job_skills;")
        print(f"   Deleted {cursor.rowcount} records")
        
        print("2. Clearing fact_job_postings...")
        cursor.execute("DELETE FROM fact_job_postings;")
        print(f"   Deleted {cursor.rowcount} records")
        
        # Clear dimension tables
        print("3. Clearing dim_skill...")
        cursor.execute("DELETE FROM dim_skill;")
        print(f"   Deleted {cursor.rowcount} records")
        
        print("4. Clearing dim_location...")
        cursor.execute("DELETE FROM dim_location;")
        print(f"   Deleted {cursor.rowcount} records")
        
        print("5. Clearing dim_company...")
        cursor.execute("DELETE FROM dim_company;")
        print(f"   Deleted {cursor.rowcount} records")
        
        print("6. Clearing dim_date...")
        cursor.execute("DELETE FROM dim_date;")
        print(f"   Deleted {cursor.rowcount} records")
        
        # Optionally clear unified_jobs (commented by default)
        # Uncomment if you want to clear unified_jobs too
        # print("7. Clearing unified_jobs...")
        # cursor.execute("DELETE FROM unified_jobs;")
        # print(f"   Deleted {cursor.rowcount} records")
        
        conn.commit()
        print("\n" + "=" * 60)
        print("✅ Data cleared successfully!")
        print("=" * 60)
        print("\nNote: unified_jobs table is kept (not cleared)")
        print("To clear unified_jobs too, uncomment the code in clear_data.py")
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error clearing data: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

def clear_all_including_unified_jobs():
    """Clear all data including unified_jobs (complete reset)"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        print("=" * 60)
        print("CLEARING ALL DATA (INCLUDING unified_jobs)")
        print("=" * 60)
        
        # Clear fact tables first
        print("\n1. Clearing fact_job_skills...")
        cursor.execute("DELETE FROM fact_job_skills;")
        print(f"   Deleted {cursor.rowcount} records")
        
        print("2. Clearing fact_job_postings...")
        cursor.execute("DELETE FROM fact_job_postings;")
        print(f"   Deleted {cursor.rowcount} records")
        
        # Clear dimension tables
        print("3. Clearing dim_skill...")
        cursor.execute("DELETE FROM dim_skill;")
        print(f"   Deleted {cursor.rowcount} records")
        
        print("4. Clearing dim_location...")
        cursor.execute("DELETE FROM dim_location;")
        print(f"   Deleted {cursor.rowcount} records")
        
        print("5. Clearing dim_company...")
        cursor.execute("DELETE FROM dim_company;")
        print(f"   Deleted {cursor.rowcount} records")
        
        print("6. Clearing dim_date...")
        cursor.execute("DELETE FROM dim_date;")
        print(f"   Deleted {cursor.rowcount} records")
        
        print("7. Clearing unified_jobs...")
        cursor.execute("DELETE FROM unified_jobs;")
        print(f"   Deleted {cursor.rowcount} records")
        
        conn.commit()
        print("\n" + "=" * 60)
        print("✅ All data cleared successfully!")
        print("=" * 60)
        
    except Exception as e:
        conn.rollback()
        print(f"\n❌ Error clearing data: {e}")
        sys.exit(1)
    finally:
        cursor.close()
        conn.close()

def main():
    """Main function"""
    # Check for --all flag to clear unified_jobs too
    clear_all = "--all" in sys.argv or "--clear-all" in sys.argv
    # Check for --yes flag to skip confirmation
    skip_confirm = "--yes" in sys.argv or "-y" in sys.argv
    
    if clear_all:
        print("⚠️  WARNING: This will clear ALL data including unified_jobs!")
        if not skip_confirm:
            try:
                response = input("Are you sure? (yes/no): ")
                if response.lower() != "yes":
                    print("Cancelled.")
                    return
            except EOFError:
                # Non-interactive mode - require --yes flag
                print("❌ Error: Cannot read input in non-interactive mode.")
                print("   Use --yes flag to skip confirmation: clear_data.py --all --yes")
                sys.exit(1)
        clear_all_including_unified_jobs()
    else:
        clear_data()

if __name__ == "__main__":
    main()

