"""
Script to create all database tables for matching system
Run this script to setup the complete database schema
"""
import os
import sys


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.create_jd_structured_table import main as create_jd_table
from utils.create_resume_structured_table import main as create_resume_table
from utils.create_embedding_tables import main as create_embedding_tables
from utils.create_matching_results_table import main as create_matching_table


def main():
    print("=" * 60)
    print("CREATING ALL DATABASE TABLES FOR MATCHING SYSTEM")
    print("=" * 60)
    
    try:
        print("\n1. Creating jd_structured table...")
        create_jd_table()
        
        print("\n2. Creating resume_structured and resume_experiences tables...")
        create_resume_table()
        
        print("\n3. Creating embedding tables...")
        create_embedding_tables()
        
        print("\n4. Creating matching_results table...")
        create_matching_table()
        
        print("\n" + "=" * 60)
        print("SUCCESS: All tables created successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nERROR: Failed to create tables: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()


