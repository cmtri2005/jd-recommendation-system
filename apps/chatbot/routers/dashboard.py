"""Dashboard API endpoints for analytics data."""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
import os
from sqlalchemy import create_engine, text
import pandas as pd
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


# Database connection
def get_db_engine():
    """Get SQLAlchemy database engine for PostgreSQL."""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5434")  # From docker-compose
    dbname = os.getenv("POSTGRES_DB", "airflow")
    user = os.getenv("POSTGRES_USER", "airflow")
    password = os.getenv("POSTGRES_PASSWORD", "airflow")

    try:
        connection_string = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        engine = create_engine(connection_string, pool_pre_ping=True)
        return engine
    except Exception as e:
        logger.error(f"Database connection error: {e}")
        return None


# Response Models
class MetricsResponse(BaseModel):
    total_jobs: int
    total_companies: int
    total_skills: int
    total_locations: int


class SkillData(BaseModel):
    skill_name: str
    job_count: int


class LocationData(BaseModel):
    city_name: str
    job_count: int


class CompanyData(BaseModel):
    company_name: str
    company_industry: Optional[str]
    job_count: int


class SourceData(BaseModel):
    source: str
    job_count: int


class LevelData(BaseModel):
    job_level: str
    job_count: int


class JobTitleData(BaseModel):
    job_title: str
    job_count: int


class IndustryData(BaseModel):
    industry: str
    company_count: int
    job_count: int


class WorkModelData(BaseModel):
    work_model: str
    job_count: int


@router.get("/api/dashboard/metrics", response_model=MetricsResponse)
async def get_metrics(
    sources: Optional[str] = Query(None, description="Comma-separated list of sources"),
    locations: Optional[str] = Query(
        None, description="Comma-separated list of locations"
    ),
    skills: Optional[str] = Query(None, description="Comma-separated list of skills"),
):
    """Get overview metrics for the dashboard."""
    engine = get_db_engine()
    if not engine:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        # Build WHERE clause
        where_clauses = []
        if sources:
            source_list = [f"'{s.strip()}'" for s in sources.split(",")]
            where_clauses.append(f"fjp.source IN ({','.join(source_list)})")

        if locations:
            loc_list = [f"'{loc.strip()}'" for loc in locations.split(",")]
            where_clauses.append(f"dl.city_name IN ({','.join(loc_list)})")

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        query = f"""
        SELECT 
            (SELECT COUNT(DISTINCT fjp.job_id) FROM fact_job_postings fjp 
             LEFT JOIN dim_location dl ON fjp.location_id = dl.location_id
             {where_sql}) as total_jobs,
            (SELECT COUNT(*) FROM dim_company) as total_companies,
            (SELECT COUNT(*) FROM dim_skill) as total_skills,
            (SELECT COUNT(*) FROM dim_location) as total_locations
        """

        with engine.connect() as conn:
            result = conn.execute(text(query))
            row = result.fetchone()

            if row:
                return MetricsResponse(
                    total_jobs=row[0] or 0,
                    total_companies=row[1] or 0,
                    total_skills=row[2] or 0,
                    total_locations=row[3] or 0,
                )
            else:
                return MetricsResponse(
                    total_jobs=0, total_companies=0, total_skills=0, total_locations=0
                )

    except Exception as e:
        logger.error(f"Error fetching metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/dashboard/top-skills", response_model=List[SkillData])
async def get_top_skills(
    limit: int = Query(20, ge=1, le=100),
    sources: Optional[str] = Query(None),
    locations: Optional[str] = Query(None),
):
    """Get top skills by job count."""
    engine = get_db_engine()
    if not engine:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        where_clauses = []
        if sources:
            source_list = [f"'{s.strip()}'" for s in sources.split(",")]
            where_clauses.append(f"fjp.source IN ({','.join(source_list)})")

        if locations:
            loc_list = [f"'{loc.strip()}'" for loc in locations.split(",")]
            where_clauses.append(f"dl.city_name IN ({','.join(loc_list)})")

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        query = f"""
        SELECT 
            ds.skill_name,
            COUNT(DISTINCT fjs.job_id) as job_count
        FROM dim_skill ds
        LEFT JOIN fact_job_skills fjs ON ds.skill_id = fjs.skill_id
        LEFT JOIN fact_job_postings fjp ON fjs.job_id = fjp.job_id
        LEFT JOIN dim_location dl ON fjp.location_id = dl.location_id
        {where_sql}
        GROUP BY ds.skill_id, ds.skill_name
        HAVING COUNT(DISTINCT fjs.job_id) > 0
        ORDER BY job_count DESC
        LIMIT {limit}
        """

        df = pd.read_sql_query(query, engine)
        return [SkillData(**row) for row in df.to_dict("records")]

    except Exception as e:
        logger.error(f"Error fetching top skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/dashboard/top-locations", response_model=List[LocationData])
async def get_top_locations(
    limit: int = Query(10, ge=1, le=50),
    sources: Optional[str] = Query(None),
):
    """Get top locations by job count."""
    engine = get_db_engine()
    if not engine:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        where_sql = ""
        if sources:
            source_list = [f"'{s.strip()}'" for s in sources.split(",")]
            where_sql = f"WHERE fjp.source IN ({','.join(source_list)})"

        query = f"""
        SELECT 
            dl.city_name,
            COUNT(fjp.job_id) as job_count
        FROM dim_location dl
        LEFT JOIN fact_job_postings fjp ON dl.location_id = fjp.location_id
        {where_sql}
        GROUP BY dl.location_id, dl.city_name
        HAVING COUNT(fjp.job_id) > 0
        ORDER BY job_count DESC
        LIMIT {limit}
        """

        df = pd.read_sql_query(query, engine)
        return [LocationData(**row) for row in df.to_dict("records")]

    except Exception as e:
        logger.error(f"Error fetching top locations: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/dashboard/top-companies", response_model=List[CompanyData])
async def get_top_companies(
    limit: int = Query(10, ge=1, le=50),
    sources: Optional[str] = Query(None),
    locations: Optional[str] = Query(None),
):
    """Get top companies by job count."""
    engine = get_db_engine()
    if not engine:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        where_clauses = []
        if sources:
            source_list = [f"'{s.strip()}'" for s in sources.split(",")]
            where_clauses.append(f"fjp.source IN ({','.join(source_list)})")

        if locations:
            loc_list = [f"'{loc.strip()}'" for loc in locations.split(",")]
            where_clauses.append(f"dl.city_name IN ({','.join(loc_list)})")

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        query = f"""
        SELECT 
            dc.company_name,
            dc.company_industry,
            COUNT(fjp.job_id) as job_count
        FROM dim_company dc
        LEFT JOIN fact_job_postings fjp ON dc.company_id = fjp.company_id
        LEFT JOIN dim_location dl ON fjp.location_id = dl.location_id
        {where_sql}
        GROUP BY dc.company_id, dc.company_name, dc.company_industry
        HAVING COUNT(fjp.job_id) > 0
        ORDER BY job_count DESC
        LIMIT {limit}
        """

        df = pd.read_sql_query(query, engine)
        return [CompanyData(**row) for row in df.to_dict("records")]

    except Exception as e:
        logger.error(f"Error fetching top companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/dashboard/jobs-by-source", response_model=List[SourceData])
async def get_jobs_by_source(
    locations: Optional[str] = Query(None),
):
    """Get job distribution by source."""
    engine = get_db_engine()
    if not engine:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        where_sql = ""
        if locations:
            loc_list = [f"'{loc.strip()}'" for loc in locations.split(",")]
            where_sql = f"WHERE dl.city_name IN ({','.join(loc_list)})"

        query = f"""
        SELECT 
            fjp.source,
            COUNT(*) as job_count
        FROM fact_job_postings fjp
        LEFT JOIN dim_location dl ON fjp.location_id = dl.location_id
        {where_sql}
        GROUP BY fjp.source
        ORDER BY job_count DESC
        """

        df = pd.read_sql_query(query, engine)
        return [SourceData(**row) for row in df.to_dict("records")]

    except Exception as e:
        logger.error(f"Error fetching jobs by source: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/dashboard/jobs-by-level", response_model=List[LevelData])
async def get_jobs_by_level(
    sources: Optional[str] = Query(None),
    locations: Optional[str] = Query(None),
):
    """Get job distribution by level."""
    engine = get_db_engine()
    if not engine:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        where_clauses = []
        if sources:
            source_list = [f"'{s.strip()}'" for s in sources.split(",")]
            where_clauses.append(f"fjp.source IN ({','.join(source_list)})")

        if locations:
            loc_list = [f"'{loc.strip()}'" for loc in locations.split(",")]
            where_clauses.append(f"dl.city_name IN ({','.join(loc_list)})")

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        query = f"""
        SELECT 
            COALESCE(fjp.job_level, 'Not Specified') as job_level,
            COUNT(*) as job_count
        FROM fact_job_postings fjp
        LEFT JOIN dim_location dl ON fjp.location_id = dl.location_id
        {where_sql}
        GROUP BY fjp.job_level
        ORDER BY job_count DESC
        """

        df = pd.read_sql_query(query, engine)
        return [LevelData(**row) for row in df.to_dict("records")]

    except Exception as e:
        logger.error(f"Error fetching jobs by level: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/dashboard/top-job-titles", response_model=List[JobTitleData])
async def get_top_job_titles(
    limit: int = Query(20, ge=1, le=100),
    sources: Optional[str] = Query(None),
    locations: Optional[str] = Query(None),
):
    """Get top job titles by job count."""
    engine = get_db_engine()
    if not engine:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        where_clauses = []
        if sources:
            source_list = [f"'{s.strip()}'" for s in sources.split(",")]
            where_clauses.append(f"fjp.source IN ({','.join(source_list)})")

        if locations:
            loc_list = [f"'{loc.strip()}'" for loc in locations.split(",")]
            where_clauses.append(f"dl.city_name IN ({','.join(loc_list)})")

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        query = f"""
        SELECT 
            COALESCE(fjp.job_title, 'Not Specified') as job_title,
            COUNT(fjp.job_id) as job_count
        FROM fact_job_postings fjp
        LEFT JOIN dim_location dl ON fjp.location_id = dl.location_id
        {where_sql}
        GROUP BY fjp.job_title
        HAVING fjp.job_title IS NOT NULL AND fjp.job_title != ''
        ORDER BY job_count DESC
        LIMIT {limit}
        """

        df = pd.read_sql_query(query, engine)
        return [JobTitleData(**row) for row in df.to_dict("records")]

    except Exception as e:
        logger.error(f"Error fetching top job titles: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/dashboard/industry-distribution", response_model=List[IndustryData])
async def get_industry_distribution(
    limit: int = Query(15, ge=1, le=50),
    sources: Optional[str] = Query(None),
    locations: Optional[str] = Query(None),
):
    """Get company distribution by industry."""
    engine = get_db_engine()
    if not engine:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        where_clauses = []
        joins = ["LEFT JOIN fact_job_postings fjp ON dc.company_id = fjp.company_id"]

        if sources:
            source_list = [f"'{s.strip()}'" for s in sources.split(",")]
            where_clauses.append(f"fjp.source IN ({','.join(source_list)})")

        if locations:
            loc_list = [f"'{loc.strip()}'" for loc in locations.split(",")]
            where_clauses.append(f"dl.city_name IN ({','.join(loc_list)})")
            joins.append(
                "LEFT JOIN dim_location dl ON fjp.location_id = dl.location_id"
            )

        join_sql = " ".join(joins)
        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        query = f"""
        SELECT 
            COALESCE(dc.company_industry, 'Not Specified') as industry,
            COUNT(DISTINCT dc.company_id) as company_count,
            COUNT(fjp.job_id) as job_count
        FROM dim_company dc
        {join_sql}
        {where_sql}
        GROUP BY dc.company_industry
        ORDER BY job_count DESC
        LIMIT {limit}
        """

        df = pd.read_sql_query(query, engine)
        return [IndustryData(**row) for row in df.to_dict("records")]

    except Exception as e:
        logger.error(f"Error fetching industry distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/api/dashboard/work-model-distribution", response_model=List[WorkModelData]
)
async def get_work_model_distribution(
    sources: Optional[str] = Query(None),
    locations: Optional[str] = Query(None),
):
    """Get job distribution by work model."""
    engine = get_db_engine()
    if not engine:
        raise HTTPException(status_code=500, detail="Database connection failed")

    try:
        where_clauses = ["fjp.work_model IS NOT NULL"]
        if sources:
            source_list = [f"'{s.strip()}'" for s in sources.split(",")]
            where_clauses.append(f"fjp.source IN ({','.join(source_list)})")

        if locations:
            loc_list = [f"'{loc.strip()}'" for loc in locations.split(",")]
            where_clauses.append(f"dl.city_name IN ({','.join(loc_list)})")

        where_sql = "WHERE " + " AND ".join(where_clauses)

        query = f"""
        SELECT 
            COALESCE(fjp.work_model, 'Not Specified') as work_model,
            COUNT(*) as job_count
        FROM fact_job_postings fjp
        LEFT JOIN dim_location dl ON fjp.location_id = dl.location_id
        {where_sql}
        GROUP BY fjp.work_model
        ORDER BY job_count DESC
        """

        df = pd.read_sql_query(query, engine)
        return [WorkModelData(**row) for row in df.to_dict("records")]

    except Exception as e:
        logger.error(f"Error fetching work model distribution: {e}")
        raise HTTPException(status_code=500, detail=str(e))
