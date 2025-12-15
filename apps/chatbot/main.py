from core.agents.resume_extract_agent import ResumeExtractAgent
from core.agents.jd_extract_agent import JDExtractAgent
from core.agents.orchestrator import Orchestrator
from utils.resume_db_writer import ResumeDBWriter
from utils.jd_db_writer import JDDBWriter


if __name__ == "__main__":
    config = Orchestrator()
    
    # Extract Resume
    print("=" * 50)
    print("EXTRACTING RESUME")
    print("=" * 50)
    resume_agent = ResumeExtractAgent("resume_agent", config.llm, config.tools)
    resume_path = "resume_jd/NGUYENMINHTRI_TEST.pdf"
    result_resume = resume_agent.extract_resume(resume_path)
    resume_data = result_resume["resume"]
    
    print(f"\nProfile Summary: {resume_data.profile_summary}")
    print(f"\nHard Skills: {resume_data.hard_skills}")
    print(f"Soft Skills: {resume_data.soft_skills}")
    print(f"\nYears of Experience: {resume_data.years_of_experience}")
    print(f"\nWork Experiences:")
    for i, exp in enumerate(resume_data.work_experiences, 1):
        print(f"  {i}. {exp.job_title} at {exp.company} ({exp.employment_period})")
        if exp.responsibilities:
            print(f"     Responsibilities:")
            for resp in exp.responsibilities:
                print(f"       - {resp}")
    print(f"\nEducations: {resume_data.educations}")
    print(f"Certifications: {resume_data.certifications}")
    print(f"Projects: {resume_data.projects}")
    print("\n" + "=" * 50)
    
    # Save Resume to Database
    print("\nSAVING RESUME TO DATABASE")
    print("=" * 50)
    try:
        resume_writer = ResumeDBWriter()
        resume_id = resume_writer.save_resume(resume_data, file_path=resume_path)
        print(f"Resume saved with ID: {resume_id}")
    except Exception as e:
        print(f"Error saving resume to database: {e}")
    
    # Extract JD
    # print("\nEXTRACTING JOB DESCRIPTIONS")
    # print("=" * 50)
    # jd_agent = JDExtractAgent("jd_agent", config.llm, config.tools)
    # jd_path = "resume_jd/url.docx"
    # result_jd = jd_agent.extract_jd(jd_path)
    # print(f"Found {result_jd['count']} job description(s):")
    # print("=" * 50)
    # for i, jd_item in enumerate(result_jd['jds'], 1):
    #     print(f"\nJD #{i}:")
    #     print(f"Job Summary: {jd_item.job_summary}")
    #     print(f"Required Hard Skills: {jd_item.require_hard_skills}")
    #     print(f"Optional Hard Skills: {jd_item.optional_hard_skills}")
    #     print(f"Required Soft Skills: {jd_item.required_soft_skills}")
    #     print(f"Optional Soft Skills: {jd_item.optional_soft_skills}")
    #     print(f"Required Work Experiences: {jd_item.required_work_experiences}")
    #     print(f"Optional Work Experiences: {jd_item.optional_work_experiences}")
    #     print(f"Required Educations: {jd_item.required_educations}")
    #     print(f"Optional Educations: {jd_item.optional_educations}")
    #     print(f"Required Years of Experience: {jd_item.required_years_of_experience}")
    #     print("-" * 50)
    #     
    #     # Save JD to Database
    #     print(f"\nSAVING JD #{i} TO DATABASE")
    #     try:
    #         jd_writer = JDDBWriter()
    #         jd_id = jd_writer.save_jd(jd_item, url=None)  # Add URL if available
    #         print(f"JD saved with ID: {jd_id}")
    #     except Exception as e:
    #         print(f"Error saving JD to database: {e}")
