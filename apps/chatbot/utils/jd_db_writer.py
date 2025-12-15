import os
import uuid
from typing import List
from datetime import datetime
from dotenv import load_dotenv
import sys

# Add apps directory to path to import crawler.utils
current_dir = os.path.dirname(os.path.abspath(__file__))
apps_dir = os.path.dirname(os.path.dirname(current_dir))
sys.path.insert(0, apps_dir)

from crawler.utils.postgresql_client import PostgreSQLClient
from schema.jd import JD


project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
load_dotenv()
load_dotenv(os.path.join(project_root, '.env'))


class JDDBWriter:
    def __init__(self):
        self.pc = PostgreSQLClient(
            database=os.getenv("POSTGRES_DB", "airflow"),
            user=os.getenv("POSTGRES_USER", "airflow"),
            password=os.getenv("POSTGRES_PASSWORD", "airflow"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", 5432))
        )

    def save_jd(self, jd: JD, url: str = None, posted_date: datetime = None) -> str:
        """
        Save JD to database. Returns jd_id.
        If JD with same url exists, update it.
        """

        jd_id = None
        if url:
            jd_id = self._get_jd_id_by_url(url)
        
        if jd_id:
            return self._update_jd(jd_id, jd, posted_date)
        else:
            return self._insert_jd(jd, url, posted_date)

    def _get_jd_id_by_url(self, url: str) -> str:
        """Get jd_id by URL if exists"""
        query = "SELECT jd_id FROM jd_structured WHERE url = %s"
        conn = self.pc.create_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(query, (url,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting JD by URL: {e}")
            return None
        finally:
            conn.close()

    def _insert_jd(self, jd: JD, url: str = None, posted_date: datetime = None) -> str:
        """Insert new JD"""
        jd_id = str(uuid.uuid4())
        
        query = """
            INSERT INTO jd_structured (
                jd_id, url, job_summary,
                require_hard_skills, optional_hard_skills,
                required_soft_skills, optional_soft_skills,
                required_work_experiences, optional_work_experiences,
                required_educations, optional_educations,
                required_years_of_experience, posted_date
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        params = (
            jd_id,
            url,
            jd.job_summary,
            jd.require_hard_skills,
            jd.optional_hard_skills,
            jd.required_soft_skills,
            jd.optional_soft_skills,
            jd.required_work_experiences,
            jd.optional_work_experiences,
            jd.required_educations,
            jd.optional_educations,
            jd.required_years_of_experience,
            posted_date
        )
        
        try:
            self.pc.execute_query(query, params)
            print(f"Successfully inserted JD with id: {jd_id}")
            return jd_id
        except Exception as e:
            print(f"Error inserting JD: {e}")
            raise

    def _update_jd(self, jd_id: str, jd: JD, posted_date: datetime = None) -> str:
        """Update existing JD"""
        query = """
            UPDATE jd_structured SET
                job_summary = %s,
                require_hard_skills = %s,
                optional_hard_skills = %s,
                required_soft_skills = %s,
                optional_soft_skills = %s,
                required_work_experiences = %s,
                optional_work_experiences = %s,
                required_educations = %s,
                optional_educations = %s,
                required_years_of_experience = %s,
                posted_date = COALESCE(%s, posted_date),
                updated_at = CURRENT_TIMESTAMP
            WHERE jd_id = %s
        """
        
        params = (
            jd.job_summary,
            jd.require_hard_skills,
            jd.optional_hard_skills,
            jd.required_soft_skills,
            jd.optional_soft_skills,
            jd.required_work_experiences,
            jd.optional_work_experiences,
            jd.required_educations,
            jd.optional_educations,
            jd.required_years_of_experience,
            posted_date,
            jd_id
        )
        
        try:
            self.pc.execute_query(query, params)
            print(f"Successfully updated JD with id: {jd_id}")
            return jd_id
        except Exception as e:
            print(f"Error updating JD: {e}")
            raise


