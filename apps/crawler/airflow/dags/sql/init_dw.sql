-- CREATE DIMENSIONS

-- Company Dimension
CREATE TABLE IF NOT EXISTS dim_company (
    company_id SERIAL PRIMARY KEY,
    company_name TEXT UNIQUE NOT NULL,
    company_industry TEXT,
    company_size TEXT,
    company_url TEXT
);

-- Location Dimension
CREATE TABLE IF NOT EXISTS dim_location (
    location_id SERIAL PRIMARY KEY,
    city_name TEXT UNIQUE NOT NULL
);

-- Date Dimension (Simplified)
CREATE TABLE IF NOT EXISTS dim_date (
    date_id DATE PRIMARY KEY,
    day INT,
    month INT,
    quarter INT,
    year INT,
    day_of_week INT
);

-- Skill Dimension
CREATE TABLE IF NOT EXISTS dim_skill (
    skill_id SERIAL PRIMARY KEY,
    skill_name TEXT UNIQUE NOT NULL
);

-- FACT TABLE
CREATE TABLE IF NOT EXISTS fact_job_postings (
    job_id TEXT PRIMARY KEY, -- Hashed ID from Spark
    company_id INT REFERENCES dim_company(company_id),
    location_id INT REFERENCES dim_location(location_id),
    date_id DATE REFERENCES dim_date(date_id),
    job_title TEXT,
    job_level TEXT,
    work_model TEXT,
    salary_raw TEXT,
    experience_years FLOAT,
    source TEXT,
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Bridge Table
CREATE TABLE IF NOT EXISTS fact_job_skills (
    job_id TEXT REFERENCES fact_job_postings(job_id),
    skill_id INT REFERENCES dim_skill(skill_id),
    PRIMARY KEY (job_id, skill_id)
);
