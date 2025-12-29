-- 1. Populate Dim Company
INSERT INTO dim_company (company_name, company_industry, company_size, company_url)
SELECT DISTINCT company_name, company_industry, company_size, company_url 
FROM unified_jobs 
WHERE company_name IS NOT NULL
ON CONFLICT (company_name) DO NOTHING;

-- 2. Populate Dim Location
INSERT INTO dim_location (city_name)
SELECT DISTINCT location_city
FROM unified_jobs 
WHERE location_city IS NOT NULL
ON CONFLICT (city_name) DO NOTHING;

-- 3. Populate Dim Skill (Unnest Array)
INSERT INTO dim_skill (skill_name)
SELECT DISTINCT s
FROM unified_jobs, UNNEST(skills) AS s
WHERE s IS NOT NULL
ON CONFLICT (skill_name) DO NOTHING;

-- 4. Populate Dim Date (Ad-hoc for now based on current date)
INSERT INTO dim_date (date_id, day, month, quarter, year, day_of_week)
SELECT DISTINCT 
    CURRENT_DATE as date_id,
    EXTRACT(DAY FROM CURRENT_DATE) as day,
    EXTRACT(MONTH FROM CURRENT_DATE) as month,
    EXTRACT(QUARTER FROM CURRENT_DATE) as quarter,
    EXTRACT(YEAR FROM CURRENT_DATE) as year,
    EXTRACT(ISODOW FROM CURRENT_DATE) as day_of_week
ON CONFLICT (date_id) DO NOTHING;

-- 5. Populate Fact Job Postings
INSERT INTO fact_job_postings (
    job_id, company_id, location_id, date_id,
    job_title, job_level, work_model, salary_raw, experience_years, source, url
)
SELECT 
    uj.job_id,
    dc.company_id,
    dl.location_id,
    CURRENT_DATE,
    uj.job_title,
    uj.job_level,
    uj.work_model,
    uj.salary,
    uj.experience_years,
    uj.source,
    uj.url
FROM unified_jobs uj
LEFT JOIN dim_company dc ON uj.company_name = dc.company_name
LEFT JOIN dim_location dl ON uj.location_city = dl.city_name
ON CONFLICT (job_id) DO UPDATE SET
    job_title = EXCLUDED.job_title,
    salary_raw = EXCLUDED.salary_raw; 

-- 6. Populate Fact Job Skills (Bridge)
INSERT INTO fact_job_skills (job_id, skill_id)
SELECT DISTINCT
    uj.job_id,
    ds.skill_id
FROM unified_jobs uj, UNNEST(uj.skills) AS s
JOIN dim_skill ds ON ds.skill_name = s
ON CONFLICT (job_id, skill_id) DO NOTHING;
