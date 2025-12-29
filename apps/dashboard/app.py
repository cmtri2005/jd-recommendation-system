import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import psycopg2
from psycopg2.extras import RealDictCursor
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from datetime import datetime, timedelta


load_dotenv()


st.set_page_config(
    page_title="JD Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


st.markdown("""
<style>
/* Force white color for all headers */
h1, h2, h3, h4, h5, h6 {
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

# Custom CSS
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        border-left: 5px solid #1f77b4;
    }
    .stMetric {
        background-color: white;
        padding: 15px;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .stMetric label {
        color: #000000 !important;
    }
    .stMetric [data-testid="stMetricValue"] {
        color: #000000 !important;
    }
    .stMetric [data-testid="stMetricLabel"] {
        color: #000000 !important;
    }
    .stMetric > div {
        color: #000000 !important;
    }
    /* Đổi màu tất cả text trong metric cards */
    div[data-testid="stMetricValue"],
    div[data-testid="stMetricLabel"],
    .stMetric p,
    .stMetric span {
        color: #000000 !important;
    }
    /* Đổi màu header - màu trắng để dễ đọc trên nền tối - với selector mạnh nhất */
    h1, h2, h3, h4, h5, h6,
    body h1, body h2, body h3, body h4, body h5, body h6,
    main h1, main h2, main h3, main h4, main h5, main h6,
    #root h1, #root h2, #root h3, #root h4, #root h5, #root h6 {
        color: #ffffff !important;
    }
    /* Đổi màu tất cả header elements trong Streamlit - với selector mạnh hơn */
    .stHeader,
    [data-testid="stHeader"],
    div[data-testid="stHeader"] h1,
    div[data-testid="stHeader"] h2,
    div[data-testid="stHeader"] h3,
    div[data-testid="stHeader"] h4,
    div[data-testid="stHeader"] h5,
    div[data-testid="stHeader"] h6,
    .element-container h1,
    .element-container h2,
    .element-container h3,
    .element-container h4,
    .element-container h5,
    .element-container h6,
    .stMarkdown h1,
    .stMarkdown h2,
    .stMarkdown h3,
    .stMarkdown h4,
    .stMarkdown h5,
    .stMarkdown h6,
    /* Selector cụ thể cho Streamlit header text */
    div[data-testid="stHeader"] > div,
    div[data-testid="stHeader"] > div > div,
    div[data-testid="stHeader"] span,
    /* Universal selector cho tất cả text trong header containers */
    [class*="stHeader"] h1,
    [class*="stHeader"] h2,
    [class*="stHeader"] h3,
    [class*="stHeader"] h4,
    [class*="stHeader"] h5,
    [class*="stHeader"] h6,
    [class*="stHeader"] * {
        color: #ffffff !important;
    }
    </style>
""", unsafe_allow_html=True)


@st.cache_resource
def get_db_engine():
    """Get SQLAlchemy database engine with caching"""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    dbname = os.getenv("POSTGRES_DB", "airflow")
    user = os.getenv("POSTGRES_USER", "airflow")
    password = os.getenv("POSTGRES_PASSWORD", "airflow")
    
    try:
        connection_string = f"postgresql://{user}:{password}@{host}:{port}/{dbname}"
        engine = create_engine(connection_string, pool_pre_ping=True)
        return engine
    except Exception as e:
        st.error(f"❌ Database connection error: {e}")
        st.info("💡 Make sure PostgreSQL is running and check your .env file")
        return None


@st.cache_resource
def get_db_connection():
    """Get database connection with caching (for direct psycopg2 usage if needed)"""
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    dbname = os.getenv("POSTGRES_DB", "airflow")
    user = os.getenv("POSTGRES_USER", "airflow")
    password = os.getenv("POSTGRES_PASSWORD", "airflow")
    
    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            dbname=dbname,
            user=user,
            password=password
        )
        return conn
    except Exception as e:
        st.error(f"❌ Database connection error: {e}")
        st.info("💡 Make sure PostgreSQL is running and check your .env file")
        return None


@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data(query):
    """Load data from database with caching using SQLAlchemy"""
    engine = get_db_engine()
    if engine is None:
        return None
    
    try:
        df = pd.read_sql_query(query, engine)
        return df
    except Exception as e:
        st.error(f"Query error: {e}")
        return None


def get_overview_metrics(selected_sources=None, selected_locations=None, selected_skills=None, selected_job_titles=None, selected_levels=None):
    """Get overview metrics with optional filters"""
    where_clauses = []
    joins = []
    
    if selected_sources and len(selected_sources) > 0:
        sources_escaped = [s.replace("'", "''") for s in selected_sources]
        sources_str = "', '".join(sources_escaped)
        where_clauses.append(f"fjp.source IN ('{sources_str}')")
    
    if selected_locations and len(selected_locations) > 0:
        locations_escaped = [loc.replace("'", "''") for loc in selected_locations]
        locations_str = "', '".join(locations_escaped)
        where_clauses.append(f"dl.city_name IN ('{locations_str}')")
        joins.append("LEFT JOIN dim_location dl ON fjp.location_id = dl.location_id")
    
    if selected_skills and len(selected_skills) > 0:
        skills_escaped = [skill.replace("'", "''") for skill in selected_skills]
        skills_str = "', '".join(skills_escaped)
        joins.append("INNER JOIN fact_job_skills fjs ON fjp.job_id = fjs.job_id")
        joins.append("INNER JOIN dim_skill ds ON fjs.skill_id = ds.skill_id")
        where_clauses.append(f"ds.skill_name IN ('{skills_str}')")
    
    if selected_job_titles and len(selected_job_titles) > 0:
        titles_escaped = [title.replace("'", "''") for title in selected_job_titles]
        titles_str = "', '".join(titles_escaped)
        where_clauses.append(f"fjp.job_title IN ('{titles_str}')")
    
    if selected_levels and len(selected_levels) > 0:
        levels_escaped = [level.replace("'", "''") for level in selected_levels]
        levels_str = "', '".join(levels_escaped)
        where_clauses.append(f"COALESCE(fjp.job_level, 'Not Specified') IN ('{levels_str}')")
    
    join_sql = " ".join(joins) if joins else ""
    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)
    
    distinct_keyword = "DISTINCT fjp.job_id" if selected_skills and len(selected_skills) > 0 else "*"
    
    query = f"""
    SELECT 
        (SELECT COUNT({distinct_keyword}) FROM fact_job_postings fjp {join_sql} {where_sql}) as total_jobs,
        (SELECT COUNT(*) FROM dim_company) as total_companies,
        (SELECT COUNT(*) FROM dim_skill) as total_skills,
        (SELECT COUNT(*) FROM dim_location) as total_locations,
        (SELECT COUNT(DISTINCT fjp.source) FROM fact_job_postings fjp {join_sql} {where_sql}) as total_sources
    """
    return load_data(query)


def get_top_companies(limit=10, selected_sources=None, selected_locations=None, selected_skills=None, selected_job_titles=None, selected_levels=None):
    """Get top companies by job count with optional filters"""
    where_clauses = []
    joins = ["LEFT JOIN fact_job_postings fjp ON dc.company_id = fjp.company_id",
             "LEFT JOIN dim_location dl ON fjp.location_id = dl.location_id"]
    
    if selected_sources and len(selected_sources) > 0:
        sources_escaped = [s.replace("'", "''") for s in selected_sources]
        sources_str = "', '".join(sources_escaped)
        where_clauses.append(f"fjp.source IN ('{sources_str}')")
    
    if selected_locations and len(selected_locations) > 0:
        locations_escaped = [loc.replace("'", "''") for loc in selected_locations]
        locations_str = "', '".join(locations_escaped)
        where_clauses.append(f"dl.city_name IN ('{locations_str}')")
    
    if selected_skills and len(selected_skills) > 0:
        skills_escaped = [skill.replace("'", "''") for skill in selected_skills]
        skills_str = "', '".join(skills_escaped)
        joins.append("INNER JOIN fact_job_skills fjs ON fjp.job_id = fjs.job_id")
        joins.append("INNER JOIN dim_skill ds ON fjs.skill_id = ds.skill_id")
        where_clauses.append(f"ds.skill_name IN ('{skills_str}')")
    
    if selected_job_titles and len(selected_job_titles) > 0:
        titles_escaped = [title.replace("'", "''") for title in selected_job_titles]
        titles_str = "', '".join(titles_escaped)
        where_clauses.append(f"fjp.job_title IN ('{titles_str}')")
    
    if selected_levels and len(selected_levels) > 0:
        levels_escaped = [level.replace("'", "''") for level in selected_levels]
        levels_str = "', '".join(levels_escaped)
        where_clauses.append(f"COALESCE(fjp.job_level, 'Not Specified') IN ('{levels_str}')")
    
    join_sql = " ".join(joins)
    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)
    
    count_expr = "COUNT(DISTINCT fjp.job_id)" if selected_skills and len(selected_skills) > 0 else "COUNT(fjp.job_id)"
    
    query = f"""
    SELECT 
        dc.company_name,
        dc.company_industry,
        dc.company_size,
        {count_expr} as job_count
    FROM dim_company dc
    {join_sql}
    {where_sql}
    GROUP BY dc.company_id, dc.company_name, dc.company_industry, dc.company_size
    ORDER BY job_count DESC
    LIMIT {limit}
    """
    return load_data(query)


def get_top_locations(limit=10, selected_sources=None, selected_locations=None, selected_skills=None, selected_job_titles=None, selected_levels=None):
    """Get top locations by job count with optional filters"""
    where_clauses = []
    joins = ["LEFT JOIN fact_job_postings fjp ON dl.location_id = fjp.location_id"]
    
    if selected_sources and len(selected_sources) > 0:
        sources_escaped = [s.replace("'", "''") for s in selected_sources]
        sources_str = "', '".join(sources_escaped)
        where_clauses.append(f"fjp.source IN ('{sources_str}')")
    
    if selected_locations and len(selected_locations) > 0:
        locations_escaped = [loc.replace("'", "''") for loc in selected_locations]
        locations_str = "', '".join(locations_escaped)
        where_clauses.append(f"dl.city_name IN ('{locations_str}')")
    
    if selected_skills and len(selected_skills) > 0:
        skills_escaped = [skill.replace("'", "''") for skill in selected_skills]
        skills_str = "', '".join(skills_escaped)
        joins.append("INNER JOIN fact_job_skills fjs ON fjp.job_id = fjs.job_id")
        joins.append("INNER JOIN dim_skill ds ON fjs.skill_id = ds.skill_id")
        where_clauses.append(f"ds.skill_name IN ('{skills_str}')")
    
    if selected_job_titles and len(selected_job_titles) > 0:
        titles_escaped = [title.replace("'", "''") for title in selected_job_titles]
        titles_str = "', '".join(titles_escaped)
        where_clauses.append(f"fjp.job_title IN ('{titles_str}')")
    
    if selected_levels and len(selected_levels) > 0:
        levels_escaped = [level.replace("'", "''") for level in selected_levels]
        levels_str = "', '".join(levels_escaped)
        where_clauses.append(f"COALESCE(fjp.job_level, 'Not Specified') IN ('{levels_str}')")
    
    join_sql = " ".join(joins)
    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)
    
    count_expr = "COUNT(DISTINCT fjp.job_id)" if selected_skills and len(selected_skills) > 0 else "COUNT(fjp.job_id)"
    
    query = f"""
    SELECT 
        dl.city_name,
        {count_expr} as job_count
    FROM dim_location dl
    {join_sql}
    {where_sql}
    GROUP BY dl.location_id, dl.city_name
    ORDER BY job_count DESC
    LIMIT {limit}
    """
    return load_data(query)


def get_top_skills(limit=20, selected_sources=None, selected_locations=None, selected_skills=None, selected_job_titles=None, selected_levels=None):
    """Get top skills by job count with optional filters"""
    where_clauses = []
    if selected_sources and len(selected_sources) > 0:
        sources_escaped = [s.replace("'", "''") for s in selected_sources]
        sources_str = "', '".join(sources_escaped)
        where_clauses.append(f"fjp.source IN ('{sources_str}')")
    
    if selected_locations and len(selected_locations) > 0:
        locations_escaped = [loc.replace("'", "''") for loc in selected_locations]
        locations_str = "', '".join(locations_escaped)
        where_clauses.append(f"dl.city_name IN ('{locations_str}')")
    

    if selected_skills and len(selected_skills) > 0:
        skills_escaped = [skill.replace("'", "''") for skill in selected_skills]
        skills_str = "', '".join(skills_escaped)
        where_clauses.append(f"ds.skill_name IN ('{skills_str}')")
    
    if selected_job_titles and len(selected_job_titles) > 0:
        titles_escaped = [title.replace("'", "''") for title in selected_job_titles]
        titles_str = "', '".join(titles_escaped)
        where_clauses.append(f"fjp.job_title IN ('{titles_str}')")
    
    if selected_levels and len(selected_levels) > 0:
        levels_escaped = [level.replace("'", "''") for level in selected_levels]
        levels_str = "', '".join(levels_escaped)
        where_clauses.append(f"COALESCE(fjp.job_level, 'Not Specified') IN ('{levels_str}')")
    
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
    ORDER BY job_count DESC
    LIMIT {limit}
    """
    return load_data(query)


def get_top_job_titles(limit=50, selected_sources=None, selected_locations=None, selected_skills=None, selected_job_titles=None, selected_levels=None):
    """Get top job titles by job count with optional filters"""
    where_clauses = []
    joins = []
    
    if selected_sources and len(selected_sources) > 0:
        sources_escaped = [s.replace("'", "''") for s in selected_sources]
        sources_str = "', '".join(sources_escaped)
        where_clauses.append(f"fjp.source IN ('{sources_str}')")
    
    if selected_locations and len(selected_locations) > 0:
        locations_escaped = [loc.replace("'", "''") for loc in selected_locations]
        locations_str = "', '".join(locations_escaped)
        where_clauses.append(f"dl.city_name IN ('{locations_str}')")
        joins.append("LEFT JOIN dim_location dl ON fjp.location_id = dl.location_id")
    
    if selected_skills and len(selected_skills) > 0:
        skills_escaped = [skill.replace("'", "''") for skill in selected_skills]
        skills_str = "', '".join(skills_escaped)
        joins.append("INNER JOIN fact_job_skills fjs ON fjp.job_id = fjs.job_id")
        joins.append("INNER JOIN dim_skill ds ON fjs.skill_id = ds.skill_id")
        where_clauses.append(f"ds.skill_name IN ('{skills_str}')")
    
    if selected_job_titles and len(selected_job_titles) > 0:
        titles_escaped = [title.replace("'", "''") for title in selected_job_titles]
        titles_str = "', '".join(titles_escaped)
        where_clauses.append(f"fjp.job_title IN ('{titles_str}')")
    
    if selected_levels and len(selected_levels) > 0:
        levels_escaped = [level.replace("'", "''") for level in selected_levels]
        levels_str = "', '".join(levels_escaped)
        where_clauses.append(f"COALESCE(fjp.job_level, 'Not Specified') IN ('{levels_str}')")
    
    join_sql = " ".join(joins) if joins else ""
    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)
    
    count_expr = "COUNT(DISTINCT fjp.job_id)" if selected_skills and len(selected_skills) > 0 else "COUNT(fjp.job_id)"
    
    query = f"""
    SELECT 
        COALESCE(fjp.job_title, 'Not Specified') as job_title,
        {count_expr} as job_count
    FROM fact_job_postings fjp
    {join_sql}
    {where_sql}
    GROUP BY fjp.job_title
    HAVING fjp.job_title IS NOT NULL AND fjp.job_title != ''
    ORDER BY job_count DESC
    LIMIT {limit}
    """
    return load_data(query)


def get_jobs_by_source(selected_locations=None, selected_skills=None, selected_job_titles=None, selected_levels=None):
    """Get job distribution by source with optional filters"""
    where_clauses = []
    joins = []
    
    if selected_locations and len(selected_locations) > 0:
        locations_escaped = [loc.replace("'", "''") for loc in selected_locations]
        locations_str = "', '".join(locations_escaped)
        where_clauses.append(f"dl.city_name IN ('{locations_str}')")
        joins.append("LEFT JOIN dim_location dl ON fjp.location_id = dl.location_id")
    
    if selected_skills and len(selected_skills) > 0:
        skills_escaped = [skill.replace("'", "''") for skill in selected_skills]
        skills_str = "', '".join(skills_escaped)
        joins.append("INNER JOIN fact_job_skills fjs ON fjp.job_id = fjs.job_id")
        joins.append("INNER JOIN dim_skill ds ON fjs.skill_id = ds.skill_id")
        where_clauses.append(f"ds.skill_name IN ('{skills_str}')")
    
    join_sql = " ".join(joins) if joins else ""
    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)
    
    count_expr = "COUNT(DISTINCT fjp.job_id)" if selected_skills and len(selected_skills) > 0 else "COUNT(*)"
    
    query = f"""
    SELECT 
        fjp.source,
        {count_expr} as job_count
    FROM fact_job_postings fjp
    {join_sql}
    {where_sql}
    GROUP BY fjp.source
    ORDER BY job_count DESC
    """
    return load_data(query)


def get_jobs_by_level(selected_sources=None, selected_locations=None, selected_skills=None, selected_job_titles=None, selected_levels=None):
    """Get job distribution by level with optional filters"""
    where_clauses = []
    joins = []
    
    if selected_sources and len(selected_sources) > 0:
        sources_escaped = [s.replace("'", "''") for s in selected_sources]
        sources_str = "', '".join(sources_escaped)
        where_clauses.append(f"fjp.source IN ('{sources_str}')")
    
    if selected_locations and len(selected_locations) > 0:
        locations_escaped = [loc.replace("'", "''") for loc in selected_locations]
        locations_str = "', '".join(locations_escaped)
        where_clauses.append(f"dl.city_name IN ('{locations_str}')")
        joins.append("LEFT JOIN dim_location dl ON fjp.location_id = dl.location_id")
    
    if selected_skills and len(selected_skills) > 0:
        skills_escaped = [skill.replace("'", "''") for skill in selected_skills]
        skills_str = "', '".join(skills_escaped)
        joins.append("INNER JOIN fact_job_skills fjs ON fjp.job_id = fjs.job_id")
        joins.append("INNER JOIN dim_skill ds ON fjs.skill_id = ds.skill_id")
        where_clauses.append(f"ds.skill_name IN ('{skills_str}')")
    
    if selected_job_titles and len(selected_job_titles) > 0:
        titles_escaped = [title.replace("'", "''") for title in selected_job_titles]
        titles_str = "', '".join(titles_escaped)
        where_clauses.append(f"fjp.job_title IN ('{titles_str}')")
    
    if selected_levels and len(selected_levels) > 0:
        levels_escaped = [level.replace("'", "''") for level in selected_levels]
        levels_str = "', '".join(levels_escaped)
        where_clauses.append(f"COALESCE(fjp.job_level, 'Not Specified') IN ('{levels_str}')")
    
    join_sql = " ".join(joins) if joins else ""
    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)
    
    count_expr = "COUNT(DISTINCT fjp.job_id)" if selected_skills and len(selected_skills) > 0 else "COUNT(*)"
    
    query = f"""
    SELECT 
        COALESCE(fjp.job_level, 'Not Specified') as job_level,
        {count_expr} as job_count
    FROM fact_job_postings fjp
    {join_sql}
    {where_sql}
    GROUP BY fjp.job_level
    ORDER BY job_count DESC
    """
    return load_data(query)


def get_job_levels(selected_sources=None, selected_locations=None, selected_skills=None, selected_job_titles=None):
    """Get list of job levels with optional filters"""
    where_clauses = []
    joins = []
    
    if selected_sources and len(selected_sources) > 0:
        sources_escaped = [s.replace("'", "''") for s in selected_sources]
        sources_str = "', '".join(sources_escaped)
        where_clauses.append(f"fjp.source IN ('{sources_str}')")
    
    if selected_locations and len(selected_locations) > 0:
        locations_escaped = [loc.replace("'", "''") for loc in selected_locations]
        locations_str = "', '".join(locations_escaped)
        where_clauses.append(f"dl.city_name IN ('{locations_str}')")
        joins.append("LEFT JOIN dim_location dl ON fjp.location_id = dl.location_id")
    
    if selected_skills and len(selected_skills) > 0:
        skills_escaped = [skill.replace("'", "''") for skill in selected_skills]
        skills_str = "', '".join(skills_escaped)
        joins.append("INNER JOIN fact_job_skills fjs ON fjp.job_id = fjs.job_id")
        joins.append("INNER JOIN dim_skill ds ON fjs.skill_id = ds.skill_id")
        where_clauses.append(f"ds.skill_name IN ('{skills_str}')")
    
    if selected_job_titles and len(selected_job_titles) > 0:
        titles_escaped = [title.replace("'", "''") for title in selected_job_titles]
        titles_str = "', '".join(titles_escaped)
        where_clauses.append(f"fjp.job_title IN ('{titles_str}')")
    
    join_sql = " ".join(joins) if joins else ""
    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)
    
    query = f"""
    SELECT 
        COALESCE(fjp.job_level, 'Not Specified') as job_level,
        COUNT(*) as job_count
    FROM fact_job_postings fjp
    {join_sql}
    {where_sql}
    GROUP BY COALESCE(fjp.job_level, 'Not Specified')
    ORDER BY job_count DESC
    """
    return load_data(query)


def get_jobs_by_work_model(selected_sources=None, selected_locations=None, selected_skills=None, selected_job_titles=None, selected_levels=None):
    """Get job distribution by work model with optional filters"""
    where_clauses = []
    joins = []
    
    if selected_sources and len(selected_sources) > 0:
        sources_escaped = [s.replace("'", "''") for s in selected_sources]
        sources_str = "', '".join(sources_escaped)
        where_clauses.append(f"fjp.source IN ('{sources_str}')")
    
    if selected_locations and len(selected_locations) > 0:
        locations_escaped = [loc.replace("'", "''") for loc in selected_locations]
        locations_str = "', '".join(locations_escaped)
        where_clauses.append(f"dl.city_name IN ('{locations_str}')")
        joins.append("LEFT JOIN dim_location dl ON fjp.location_id = dl.location_id")
    
    if selected_skills and len(selected_skills) > 0:
        skills_escaped = [skill.replace("'", "''") for skill in selected_skills]
        skills_str = "', '".join(skills_escaped)
        joins.append("INNER JOIN fact_job_skills fjs ON fjp.job_id = fjs.job_id")
        joins.append("INNER JOIN dim_skill ds ON fjs.skill_id = ds.skill_id")
        where_clauses.append(f"ds.skill_name IN ('{skills_str}')")
    
    if selected_job_titles and len(selected_job_titles) > 0:
        titles_escaped = [title.replace("'", "''") for title in selected_job_titles]
        titles_str = "', '".join(titles_escaped)
        where_clauses.append(f"fjp.job_title IN ('{titles_str}')")
    
    if selected_levels and len(selected_levels) > 0:
        levels_escaped = [level.replace("'", "''") for level in selected_levels]
        levels_str = "', '".join(levels_escaped)
        where_clauses.append(f"COALESCE(fjp.job_level, 'Not Specified') IN ('{levels_str}')")
    
    join_sql = " ".join(joins) if joins else ""
    where_clauses.append("fjp.work_model IS NOT NULL")
    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)
    
    count_expr = "COUNT(DISTINCT fjp.job_id)" if selected_skills and len(selected_skills) > 0 else "COUNT(*)"
    
    query = f"""
    SELECT 
        COALESCE(fjp.work_model, 'Not Specified') as work_model,
        {count_expr} as job_count
    FROM fact_job_postings fjp
    {join_sql}
    {where_sql}
    GROUP BY fjp.work_model
    ORDER BY job_count DESC
    """
    return load_data(query)


def get_skills_trend():
    """Get skills trend (top skills with their job counts)"""
    query = """
    SELECT 
        ds.skill_name,
        COUNT(DISTINCT fjs.job_id) as job_count
    FROM dim_skill ds
    LEFT JOIN fact_job_skills fjs ON ds.skill_id = fjs.skill_id
    GROUP BY ds.skill_id, ds.skill_name
    HAVING COUNT(DISTINCT fjs.job_id) > 0
    ORDER BY job_count DESC
    LIMIT 30
    """
    return load_data(query)


def get_company_industry_distribution(selected_sources=None, selected_locations=None, selected_skills=None, selected_job_titles=None, selected_levels=None):
    """Get company distribution by industry with optional filters"""
    where_clauses = []
    joins = ["LEFT JOIN fact_job_postings fjp ON dc.company_id = fjp.company_id"]
    
    if selected_sources and len(selected_sources) > 0:
        sources_escaped = [s.replace("'", "''") for s in selected_sources]
        sources_str = "', '".join(sources_escaped)
        where_clauses.append(f"fjp.source IN ('{sources_str}')")
    
    if selected_locations and len(selected_locations) > 0:
        locations_escaped = [loc.replace("'", "''") for loc in selected_locations]
        locations_str = "', '".join(locations_escaped)
        where_clauses.append(f"dl.city_name IN ('{locations_str}')")
        joins.append("LEFT JOIN dim_location dl ON fjp.location_id = dl.location_id")
    
    if selected_skills and len(selected_skills) > 0:
        skills_escaped = [skill.replace("'", "''") for skill in selected_skills]
        skills_str = "', '".join(skills_escaped)
        joins.append("INNER JOIN fact_job_skills fjs ON fjp.job_id = fjs.job_id")
        joins.append("INNER JOIN dim_skill ds ON fjs.skill_id = ds.skill_id")
        where_clauses.append(f"ds.skill_name IN ('{skills_str}')")
    
    if selected_job_titles and len(selected_job_titles) > 0:

        titles_escaped = [title.replace("'", "''") for title in selected_job_titles]
        titles_str = "', '".join(titles_escaped)
        where_clauses.append(f"fjp.job_title IN ('{titles_str}')")
    
    if selected_levels and len(selected_levels) > 0:
        levels_escaped = [level.replace("'", "''") for level in selected_levels]
        levels_str = "', '".join(levels_escaped)
        where_clauses.append(f"COALESCE(fjp.job_level, 'Not Specified') IN ('{levels_str}')")
    
    join_sql = " ".join(joins)
    where_sql = ""
    if where_clauses:
        where_sql = "WHERE " + " AND ".join(where_clauses)
    
    count_expr = "COUNT(DISTINCT fjp.job_id)" if selected_skills and len(selected_skills) > 0 else "COUNT(fjp.job_id)"
    
    query = f"""
    SELECT 
        COALESCE(dc.company_industry, 'Not Specified') as industry,
        COUNT(DISTINCT dc.company_id) as company_count,
        {count_expr} as job_count
    FROM dim_company dc
    {join_sql}
    {where_sql}
    GROUP BY dc.company_industry
    ORDER BY job_count DESC
    LIMIT 15
    """
    return load_data(query)


def main():

    st.title("📊 JD Analytics Dashboard")
    st.markdown("---")
    
    with st.sidebar:
        st.header("🔍 Filters")

        source_data = get_jobs_by_source(selected_locations=None, selected_skills=None, selected_job_titles=None, selected_levels=None)
        if source_data is not None and not source_data.empty:
            selected_sources = st.multiselect(
                "Select Sources",
                options=source_data['source'].tolist(),
                default=source_data['source'].tolist(),
                help="Filter data by job source (TopCV, ITViec, etc.)"
            )
        else:
            selected_sources = []
        
        location_data = get_top_locations(100, selected_sources=None, selected_locations=None, selected_skills=None, selected_job_titles=None, selected_levels=None)
        if location_data is not None and not location_data.empty:
            selected_locations = st.multiselect(
                "Select Locations",
                options=location_data['city_name'].tolist(),
                default=[],
                help="Filter data by city/location. Leave empty to show all locations."
            )
        else:
            selected_locations = []
        
        skills_data = get_top_skills(100, selected_sources=None, selected_locations=None, selected_skills=None, selected_job_titles=None, selected_levels=None)
        if skills_data is not None and not skills_data.empty:
            selected_skills = st.multiselect(
                "Select Skills",
                options=skills_data['skill_name'].tolist(),
                default=[],
                help="Filter data by required skills. Leave empty to show all skills."
            )
        else:
            selected_skills = []
        

        job_titles_data = get_top_job_titles(100, selected_sources=None, selected_locations=None, selected_skills=None, selected_job_titles=None, selected_levels=None)
        if job_titles_data is not None and not job_titles_data.empty:
            selected_job_titles = st.multiselect(
                "Select Job Titles",
                options=job_titles_data['job_title'].tolist(),
                default=[],
                help="Filter data by job title (e.g., Data Engineer, Backend Developer). Leave empty to show all job titles."
            )
        else:
            selected_job_titles = []
        

        level_data = get_job_levels(selected_sources=None, selected_locations=None, selected_skills=None, selected_job_titles=None)
        if level_data is not None and not level_data.empty:
            selected_levels = st.multiselect(
                "Select Job Levels",
                options=level_data['job_level'].tolist(),
                default=[],
                help="Filter data by job level (e.g., Junior, Senior, Mid-level). Leave empty to show all levels."
            )
        else:
            selected_levels = []
        
        st.markdown("---")
        st.markdown("### 📊 Data Info")
        st.caption("Data is cached for 5 minutes")
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("### 📥 Export Data")
        st.caption("Export current data to CSV")
        

        if st.button("📋 Export Jobs"):
            st.session_state['export_jobs'] = True
        if st.button("🏢 Export Companies"):
            st.session_state['export_companies'] = True
        if st.button("💻 Export Skills"):
            st.session_state['export_skills'] = True
    

    engine = get_db_engine()
    if engine is None:
        st.stop()
    

    if st.session_state.get('export_jobs', False):
        jobs_export_query = """
        SELECT 
            fjp.job_id,
            fjp.job_title,
            dc.company_name,
            dl.city_name,
            fjp.job_level,
            fjp.work_model,
            fjp.source,
            fjp.created_at
        FROM fact_job_postings fjp
        LEFT JOIN dim_company dc ON fjp.company_id = dc.company_id
        LEFT JOIN dim_location dl ON fjp.location_id = dl.location_id
        ORDER BY fjp.created_at DESC
        """
        jobs_export_df = load_data(jobs_export_query)
        if jobs_export_df is not None and not jobs_export_df.empty:
            csv = jobs_export_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Jobs CSV",
                data=csv,
                file_name=f"jobs_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_jobs"
            )
        st.session_state['export_jobs'] = False
    
    if st.session_state.get('export_companies', False):
        companies_export_query = """
        SELECT 
            dc.company_name,
            dc.company_industry,
            dc.company_size,
            COUNT(fjp.job_id) as job_count
        FROM dim_company dc
        LEFT JOIN fact_job_postings fjp ON dc.company_id = fjp.company_id
        GROUP BY dc.company_id, dc.company_name, dc.company_industry, dc.company_size
        ORDER BY job_count DESC
        """
        companies_export_df = load_data(companies_export_query)
        if companies_export_df is not None and not companies_export_df.empty:
            csv = companies_export_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Companies CSV",
                data=csv,
                file_name=f"companies_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_companies"
            )
        st.session_state['export_companies'] = False
    
    if st.session_state.get('export_skills', False):
        skills_export_query = """
        SELECT 
            ds.skill_name,
            COUNT(DISTINCT fjs.job_id) as job_count
        FROM dim_skill ds
        LEFT JOIN fact_job_skills fjs ON ds.skill_id = fjs.skill_id
        GROUP BY ds.skill_id, ds.skill_name
        ORDER BY job_count DESC
        """
        skills_export_df = load_data(skills_export_query)
        if skills_export_df is not None and not skills_export_df.empty:
            csv = skills_export_df.to_csv(index=False)
            st.download_button(
                label="📥 Download Skills CSV",
                data=csv,
                file_name=f"skills_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                key="download_skills"
            )
        st.session_state['export_skills'] = False
    
    # Overview Metrics
    st.header("📈 Overview Metrics")
    metrics = get_overview_metrics(selected_sources=selected_sources, selected_locations=selected_locations, selected_skills=selected_skills, selected_job_titles=selected_job_titles, selected_levels=selected_levels)
    
    if metrics is not None and not metrics.empty:
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric(
                label="Total Jobs",
                value=f"{metrics['total_jobs'].iloc[0]:,}",
                delta=None
            )
        
        with col2:
            st.metric(
                label="Total Companies",
                value=f"{metrics['total_companies'].iloc[0]:,}",
                delta=None
            )
        
        with col3:
            st.metric(
                label="Total Skills",
                value=f"{metrics['total_skills'].iloc[0]:,}",
                delta=None
            )
        
        with col4:
            st.metric(
                label="Total Locations",
                value=f"{metrics['total_locations'].iloc[0]:,}",
                delta=None
            )
        
        with col5:
            st.metric(
                label="Data Sources",
                value=f"{metrics['total_sources'].iloc[0]:,}",
                delta=None
            )
    
    st.markdown("---")
    
    # Charts Section
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Jobs by Source")
        source_data = get_jobs_by_source(selected_locations=selected_locations, selected_skills=selected_skills, selected_job_titles=selected_job_titles, selected_levels=selected_levels)
        if source_data is not None and not source_data.empty:
            fig = px.pie(
                source_data,
                values='job_count',
                names='source',
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(showlegend=True, height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")
    
    with col2:
        st.subheader("💼 Jobs by Level")
        level_data = get_jobs_by_level(selected_sources=selected_sources, selected_locations=selected_locations, selected_skills=selected_skills, selected_job_titles=selected_job_titles, selected_levels=selected_levels)
        if level_data is not None and not level_data.empty:
            fig = px.bar(
                level_data,
                x='job_level',
                y='job_count',
                color='job_count',
                color_continuous_scale='Blues',
                labels={'job_level': 'Job Level', 'job_count': 'Number of Jobs'}
            )
            fig.update_layout(showlegend=False, height=400, xaxis_tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No data available")
    
    st.markdown("---")
    
    # Top Companies
    st.header("🏢 Top Companies")
    top_companies = get_top_companies(15, selected_sources=selected_sources, selected_locations=selected_locations, selected_skills=selected_skills, selected_job_titles=selected_job_titles, selected_levels=selected_levels)
    
    if top_companies is not None and not top_companies.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Format số liệu để hiển thị
            top_companies_display = top_companies.copy()
            top_companies_display['job_count_text'] = top_companies_display['job_count'].apply(lambda x: f'{int(x):,}')
            
            fig = px.bar(
                top_companies_display,
                x='job_count',
                y='company_name',
                orientation='h',
                color='job_count',
                color_continuous_scale='Viridis',
                labels={'job_count': 'Number of Jobs', 'company_name': 'Company'},
                text='job_count_text'
            )
            fig.update_traces(
                texttemplate='%{text}',
                textposition='outside',
                textfont=dict(size=12, color='white')
            )
            # Thêm margin và range để text không bị cắt
            max_jobs = top_companies['job_count'].max()
            fig.update_layout(
                showlegend=False,
                height=500,
                yaxis={'categoryorder': 'total ascending'},
                xaxis_title='Number of Jobs',
                yaxis_title='Company',
                margin=dict(l=10, r=100, t=10, b=10),
                xaxis=dict(range=[0, max_jobs * 1.2])  
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Company Details")
            for idx, row in top_companies.head(10).iterrows():
                with st.expander(f"{row['company_name']}"):
                    st.write(f"**Industry:** {row['company_industry'] or 'N/A'}")
                    st.write(f"**Size:** {row['company_size'] or 'N/A'}")
                    st.write(f"**Jobs:** {row['job_count']}")
    else:
        st.info("No company data available")
    
    st.markdown("---")
    
    # Top Locations
    st.header("📍 Top Locations")
    top_locations = get_top_locations(15, selected_sources=selected_sources, selected_locations=selected_locations, selected_skills=selected_skills, selected_job_titles=selected_job_titles, selected_levels=selected_levels)
    
    if top_locations is not None and not top_locations.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            top_locations_display = top_locations.copy()
            top_locations_display['job_count_text'] = top_locations_display['job_count'].apply(lambda x: f'{int(x):,}')
            
            fig = px.bar(
                top_locations_display,
                x='city_name',
                y='job_count',
                color='job_count',
                color_continuous_scale='Greens',
                labels={'city_name': 'City', 'job_count': 'Number of Jobs'},
                text='job_count_text'
            )
            fig.update_traces(
                texttemplate='%{text}',
                textposition='outside',
                textfont=dict(size=12, color='white')
            )
            max_jobs = top_locations['job_count'].max()
            fig.update_layout(
                showlegend=False,
                height=400,
                xaxis_tickangle=-45,
                xaxis_title='City',
                yaxis_title='Number of Jobs',
                margin=dict(l=10, r=10, t=80, b=10),
                yaxis=dict(range=[0, max_jobs * 1.15])
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Location Stats")
            st.dataframe(
                top_locations.set_index('city_name'),
                use_container_width=True
            )
    else:
        st.info("No location data available")
    
    st.markdown("---")
    
    # Top Skills
    st.header("💻 Top Skills")
    top_skills = get_top_skills(25, selected_sources=selected_sources, selected_locations=selected_locations, selected_skills=selected_skills, selected_job_titles=selected_job_titles, selected_levels=selected_levels)
    
    if top_skills is not None and not top_skills.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            top_skills_display = top_skills.copy()
            top_skills_display['job_count_text'] = top_skills_display['job_count'].apply(lambda x: f'{int(x):,}')
            
            fig = px.bar(
                top_skills_display,
                x='job_count',
                y='skill_name',
                orientation='h',
                color='job_count',
                color_continuous_scale='Oranges',
                labels={'job_count': 'Number of Jobs', 'skill_name': 'Skill'},
                text='job_count_text'
            )
            fig.update_traces(
                texttemplate='%{text}',
                textposition='outside',
                textfont=dict(size=12, color='white')
            )
            max_jobs = top_skills['job_count'].max()
            fig.update_layout(
                showlegend=False,
                height=600,
                yaxis={'categoryorder': 'total ascending'},
                xaxis_title='Number of Jobs',
                yaxis_title='Skill',
                margin=dict(l=10, r=100, t=10, b=10),
                xaxis=dict(range=[0, max_jobs * 1.2])  
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Skill Rankings")
            st.dataframe(
                top_skills[['skill_name', 'job_count']].set_index('skill_name'),
                use_container_width=True
            )
    else:
        st.info("No skill data available")
    
    st.markdown("---")
    
    # Top Job Titles
    st.header("💼 Top Job Titles")
    top_job_titles = get_top_job_titles(20, selected_sources=selected_sources, selected_locations=selected_locations, selected_skills=selected_skills, selected_job_titles=selected_job_titles, selected_levels=selected_levels)
    
    if top_job_titles is not None and not top_job_titles.empty:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Format số liệu để hiển thị
            top_job_titles_display = top_job_titles.copy()
            top_job_titles_display['job_count_text'] = top_job_titles_display['job_count'].apply(lambda x: f'{int(x):,}')
            
            fig = px.bar(
                top_job_titles_display,
                x='job_count',
                y='job_title',
                orientation='h',
                color='job_count',
                color_continuous_scale='Purples',
                labels={'job_count': 'Number of Jobs', 'job_title': 'Job Title'},
                text='job_count_text'
            )
            fig.update_traces(
                texttemplate='%{text}',
                textposition='outside',
                textfont=dict(size=12, color='white')
            )
            max_jobs = top_job_titles['job_count'].max()
            fig.update_layout(
                showlegend=False,
                height=600,
                yaxis={'categoryorder': 'total ascending'},
                xaxis_title='Number of Jobs',
                yaxis_title='Job Title',
                margin=dict(l=10, r=100, t=10, b=10),
                xaxis=dict(range=[0, max_jobs * 1.2])  
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("Job Title Rankings")
            st.dataframe(
                top_job_titles[['job_title', 'job_count']].set_index('job_title'),
                use_container_width=True
            )
    else:
        st.info("No job title data available")
    
    st.markdown("---")
    
    # Additional Charts
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏭 Industry Distribution")
        industry_data = get_company_industry_distribution(selected_sources=selected_sources, selected_locations=selected_locations, selected_skills=selected_skills, selected_job_titles=selected_job_titles, selected_levels=selected_levels)
        if industry_data is not None and not industry_data.empty:
            fig = px.treemap(
                industry_data,
                path=['industry'],
                values='job_count',
                color='job_count',
                color_continuous_scale='Reds',
                labels={'job_count': 'Jobs', 'industry': 'Industry'}
            )
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No industry data available")
    
    with col2:
        st.subheader("🏠 Work Model Distribution")
        work_model_data = get_jobs_by_work_model(selected_sources=selected_sources, selected_locations=selected_locations, selected_skills=selected_skills, selected_job_titles=selected_job_titles, selected_levels=selected_levels)
        if work_model_data is not None and not work_model_data.empty:
            fig = px.pie(
                work_model_data,
                values='job_count',
                names='work_model',
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(showlegend=True, height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No work model data available")
    
    st.markdown("---")
    
    # Raw Data Tables (Optional - in expander)
    with st.expander("📋 View Raw Data"):
        tab1, tab2, tab3 = st.tabs(["Jobs", "Companies", "Skills"])
        
        with tab1:
            jobs_query = """
            SELECT 
                fjp.job_id,
                fjp.job_title,
                dc.company_name,
                dl.city_name,
                fjp.job_level,
                fjp.work_model,
                fjp.source
            FROM fact_job_postings fjp
            LEFT JOIN dim_company dc ON fjp.company_id = dc.company_id
            LEFT JOIN dim_location dl ON fjp.location_id = dl.location_id
            ORDER BY fjp.created_at DESC
            LIMIT 100
            """
            jobs_df = load_data(jobs_query)
            if jobs_df is not None and not jobs_df.empty:
                st.dataframe(jobs_df, use_container_width=True)
            else:
                st.info("No job data available")
        
        with tab2:
            companies_query = """
            SELECT 
                company_name,
                company_industry,
                company_size,
                company_url
            FROM dim_company
            ORDER BY company_name
            LIMIT 100
            """
            companies_df = load_data(companies_query)
            if companies_df is not None and not companies_df.empty:
                st.dataframe(companies_df, use_container_width=True)
            else:
                st.info("No company data available")
        
        with tab3:
            skills_query = """
            SELECT 
                skill_name,
                COUNT(DISTINCT fjs.job_id) as job_count
            FROM dim_skill ds
            LEFT JOIN fact_job_skills fjs ON ds.skill_id = fjs.skill_id
            GROUP BY ds.skill_id, ds.skill_name
            ORDER BY job_count DESC
            LIMIT 100
            """
            skills_df = load_data(skills_query)
            if skills_df is not None and not skills_df.empty:
                st.dataframe(skills_df, use_container_width=True)
            else:
                st.info("No skill data available")
    
    st.markdown("---")
    
    # Footer
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
        <p>JD Recommendation System Dashboard | Last updated: {}</p>
    </div>
    """.format(datetime.now().strftime("%Y-%m-%d %H:%M:%S")), unsafe_allow_html=True)


if __name__ == "__main__":
    main()

