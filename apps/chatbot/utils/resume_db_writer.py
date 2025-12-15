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
from schema.resume import Resume
from schema.experience import Experience

# Load .env from project root
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_dir))))
load_dotenv()
load_dotenv(os.path.join(project_root, '.env'))


class ResumeDBWriter:
    def __init__(self):
        self.pc = PostgreSQLClient(
            database=os.getenv("POSTGRES_DB", "airflow"),
            user=os.getenv("POSTGRES_USER", "airflow"),
            password=os.getenv("POSTGRES_PASSWORD", "airflow"),
            host=os.getenv("POSTGRES_HOST", "localhost"),
            port=int(os.getenv("POSTGRES_PORT", 5432))
        )

    def save_resume(self, resume: Resume, file_path: str = None) -> str:
        """
        Save Resume to database. Returns resume_id.
        If resume with same file_path exists, update it.
        """
        
        resume_id = None
        if file_path:
            resume_id = self._get_resume_id_by_file_path(file_path)
        
        if resume_id:
            return self._update_resume(resume_id, resume, file_path)
        else:
            return self._insert_resume(resume, file_path)

    def _get_resume_id_by_file_path(self, file_path: str) -> str:
        """Get resume_id by file_path if exists"""
        query = "SELECT resume_id FROM resume_structured WHERE file_path = %s"
        conn = self.pc.create_conn()
        cursor = conn.cursor()
        try:
            cursor.execute(query, (file_path,))
            result = cursor.fetchone()
            return result[0] if result else None
        except Exception as e:
            print(f"Error getting resume by file_path: {e}")
            return None
        finally:
            conn.close()

    def _insert_resume(self, resume: Resume, file_path: str = None) -> str:
        """Insert new resume"""
        resume_id = str(uuid.uuid4())
        
        
        query = """
            INSERT INTO resume_structured (
                resume_id, file_path, profile_summary,
                hard_skills, soft_skills, educations,
                years_of_experience, certifications, projects
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
        """
        
        params = (
            resume_id,
            file_path,
            resume.profile_summary,
            resume.hard_skills,
            resume.soft_skills,
            resume.educations,
            resume.years_of_experience,
            resume.certifications,
            resume.projects
        )
        
        try:
            self.pc.execute_query(query, params)
            
            
            if resume.work_experiences:
                self._insert_experiences(resume_id, resume.work_experiences)
            
            print(f"Successfully inserted resume with id: {resume_id}")
            return resume_id
        except Exception as e:
            print(f"Error inserting resume: {e}")
            raise

    def _insert_experiences(self, resume_id: str, experiences: List[Experience]):
        """Insert work experiences for a resume"""
        if not experiences:
            return
        
        query = """
            INSERT INTO resume_experiences (
                resume_id, job_title, company, employment_period, responsibilities
            ) VALUES (
                %s, %s, %s, %s, %s
            )
        """
        
        conn = self.pc.create_conn()
        cursor = conn.cursor()
        
        try:
            for exp in experiences:
                params = (
                    resume_id,
                    exp.job_title,
                    exp.company,
                    exp.employment_period,
                    exp.responsibilities
                )
                cursor.execute(query, params)
            
            conn.commit()
            print(f"Successfully inserted {len(experiences)} experiences")
        except Exception as e:
            conn.rollback()
            print(f"Error inserting experiences: {e}")
            raise
        finally:
            conn.close()

    def _update_resume(self, resume_id: str, resume: Resume, file_path: str = None) -> str:
        """Update existing resume"""
        
        query = """
            UPDATE resume_structured SET
                file_path = COALESCE(%s, file_path),
                profile_summary = %s,
                hard_skills = %s,
                soft_skills = %s,
                educations = %s,
                years_of_experience = %s,
                certifications = %s,
                projects = %s,
                updated_at = CURRENT_TIMESTAMP
            WHERE resume_id = %s
        """
        
        params = (
            file_path,
            resume.profile_summary,
            resume.hard_skills,
            resume.soft_skills,
            resume.educations,
            resume.years_of_experience,
            resume.certifications,
            resume.projects,
            resume_id
        )
        
        try:
            self.pc.execute_query(query, params)
            
            
            self._delete_experiences(resume_id)
            if resume.work_experiences:
                self._insert_experiences(resume_id, resume.work_experiences)
            
            print(f"Successfully updated resume with id: {resume_id}")
            return resume_id
        except Exception as e:
            print(f"Error updating resume: {e}")
            raise

    def _delete_experiences(self, resume_id: str):
        """Delete all experiences for a resume"""
        query = "DELETE FROM resume_experiences WHERE resume_id = %s"
        try:
            self.pc.execute_query(query, (resume_id,))
        except Exception as e:
            print(f"Error deleting experiences: {e}")


