-- Fix Job Level directly in Fact Table (fact_job_postings)

UPDATE fact_job_postings
SET job_level = CASE
    -- 1. Intern
    WHEN LOWER(COALESCE(job_level, '')) ~ 'intern|thực tập' 
      OR LOWER(job_title) ~ 'intern|thực tập' THEN 'Intern'
      
    -- 2. Fresher
    WHEN LOWER(COALESCE(job_level, '')) ~ 'fresher|mới|graduate|entry'
      OR LOWER(job_title) ~ 'fresher|mới|graduate|entry' THEN 'Fresher'
    
    -- 3. Lead
    WHEN LOWER(COALESCE(job_level, '')) ~ 'lead|leader|tech lead|team lead|trưởng|quản lý|product owner|delivery lead'
      OR LOWER(job_title) ~ 'lead|leader|trưởng nhóm|delivery lead|product owner' THEN 'Lead'

    -- 4. Manager
    WHEN LOWER(COALESCE(job_level, '')) ~ 'manager|head|chief|director|vp|cto|phó phòng|giám đốc'
      OR LOWER(job_title) ~ 'manager|manage|head|chief|director|vp|cto|phó phòng|giám đốc|trưởng phòng' THEN 'Manager'

    -- 5. Senior
    WHEN LOWER(COALESCE(job_level, '')) ~ 'senior|sr|expert|principal|chuyên viên|cao cấp|architect'
      OR LOWER(job_title) ~ 'senior|sr|expert|principal|cao cấp|architect' THEN 'Senior'

    -- 6. Middle
    WHEN LOWER(COALESCE(job_level, '')) ~ 'middle|mid|senior staff|trung cấp|experienced'
      OR LOWER(job_title) ~ 'middle|mid|trung cấp' THEN 'Middle'

    -- 7. Junior (Catch-all for 'dev', 'staff', 'engineer')
    WHEN LOWER(COALESCE(job_level, '')) ~ 'junior|jr|nhân viên|staff|associate|developer|lập trình viên'
      OR LOWER(job_title) ~ 'junior|jr|nhân viên|staff|associate|developer|lập trình viên|kỹ sư|engineer|chuyên viên' THEN 'Junior'

    -- Default Aggressive
    ELSE 'Junior'
END;
-- WHERE job_level NOT IN ('Intern', 'Fresher', 'Junior', 'Middle', 'Senior', 'Lead', 'Manager'); 
-- Run on all to enforce consistency
