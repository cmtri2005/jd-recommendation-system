-- Drop table if exists (to ensure clean state)
DROP TABLE IF EXISTS unified_jobs CASCADE;

-- Create unified_jobs table (staging table for unified job data from TopCV and ITViec)
CREATE TABLE unified_jobs (
    job_id TEXT PRIMARY KEY, -- SHA256 hash of URL
    source TEXT NOT NULL, -- 'TopCV' or 'ITViec'
    url TEXT UNIQUE NOT NULL,
    -- Company Attributes
    company_name TEXT,
    company_industry TEXT,
    company_size TEXT,
    company_url TEXT,
    -- Job Attributes
    job_title TEXT,
    job_description TEXT,
    job_requirements TEXT,
    job_benefits TEXT,
    salary TEXT,
    job_level TEXT,
    experience_years FLOAT,
    -- Skills & Location
    skills TEXT[], -- Array of skills
    location_city TEXT,
    work_model TEXT,
    -- Metadata
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_unified_jobs_source ON unified_jobs(source);
CREATE INDEX IF NOT EXISTS idx_unified_jobs_company ON unified_jobs(company_name);
CREATE INDEX IF NOT EXISTS idx_unified_jobs_location ON unified_jobs(location_city);
CREATE INDEX IF NOT EXISTS idx_unified_jobs_created ON unified_jobs(created_at DESC);

