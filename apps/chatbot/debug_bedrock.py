import os
import json
import logging
from dotenv import load_dotenv

from langchain_core.prompts import PromptTemplate
from langchain_aws import ChatBedrock
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
DOTENV_PATH = os.path.join(ROOT_DIR, ".env")
load_dotenv(DOTENV_PATH)


class JobEnrichment(BaseModel):
    job_level: str = Field(
        description="One of: Intern, Fresher, Junior, Senior, Lead, Manager, Director. Infer mainly from Job Title. Default to 'Junior' if unsure."
    )
    experience_years: float = Field(
        description="Years of experience mentioned in title or skills text. 0.0 if not found."
    )
    skills: list[str] = Field(
        description="Normalized list of technical skills found in the input (e.g. 'React.js' -> 'ReactJS', 'Aws' -> 'AWS')."
    )


def main():
    llm = ChatBedrock(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        model_kwargs={"temperature": 0.0, "max_tokens": 512},
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
    )

    parser = JsonOutputParser(pydantic_object=JobEnrichment)

    prompt = PromptTemplate(
        template="""Analyze the following job information to extract 3 fields: 
        1. 'job_level': (Intern, Fresher, Junior, Senior, Lead, Manager, Director) based on the Title.
        2. 'experience_years': Number of years required (float).
        3. 'skills': Clean and standard list of technical skills mentioned in the source tags.
        
        Job Title: {title}
        Source Skills/Tags: {source_skills}
        
        Return JSON.
        {format_instructions}
        """,
        input_variables=["title", "source_skills"],
        partial_variables={"format_instructions": parser.get_format_instructions()},
    )

    chain = prompt | llm | parser

    # User provided record
    record = {
        "url": "https://itviec.com/it-jobs/senior-backend-developer-java-vinamilk-0248",
        "job_title": "Senior Backend Developer (Java)",
        "work_model": "At office",
        "address": "Vinamilk Tower, 10 Tan Trao St., Tan Phu Ward., , District 7, Ho Chi Minh",
        "required_skills": ["Java", "Spring Boot", "PostgreSql", "AWS"],
        "time_posted_raw": "2025-12-26",
        "job_description": "As a backend engineer, you will be working within a specific problem where you will design, develop, and deploy backend services with a focus on scalability, high availability, and low latency.\nSolving complex technical and business problems and learning new technology and frameworks.\nBe part of a team that will take full responsibility for the features you own.\nDesign, develop, test, deploy, monitor, and improve, you are responsible for the full life-cycle of your product – build it, own it.",
        "your_skills_experience": "Must Have\nBachelor in Computer Sciences or related field or equivalent experience.\nAt least 5-year experience in working in enterprise and digital domains.\nStrong Java experience, Git source control, and Git Flow branching model.\nDeep understanding of API and REST services, as well as integration to mobile, web.\nSolid understanding of object-oriented programming.\nStrong problem-solving skills, able to work individually as well as in a team.\nGood English communication (read, write).\nNice to have\nExperience using third-party libraries like React and scripting like Groovy.\nStrong experience in Web development (HTML, CSS, Angular or similar).\nExperience in AWS, Ansible, Docker, K8s is a big plus.\nGood English listening and speaking is a big plus.",
        "company_name": "Vinamilk",
        "company_url": "https://itviec.com/companies/vinamilk",
        "company_type": "Non-IT",
        "company_industry": "Food and Beverage",
        "company_size": "1000+ employees",
        "country": "Vietnam",
        "working_days": "Monday - Friday",
        "overtime_policy": "No OT",
        "employment_benefits": [
            "Competitive salary and benefits on Top in VietNam.",
            "Attractive 13th-month salary and high performance bonus in the year.",
            "Annual performance review for salary raise and promotion.",
            "Premium private insurance with a discount for family members.",
            "Annual health check.",
            "Company trips and team buildings.",
            "Gifts on special accession: individual /company birthday, Tet, and Holidays.",
            "Internal activities, sport, and social clubs, gym, yoga, swimming…",
            "Opportunity to train both technical and soft skills to develop your career path.",
        ],
        "year": 2025.0,
        "month": 12.0,
        "day": 26.0,
        "normalized_level": None,
        "normalized_exp_years": None,
        "normalized_skills": [],
    }

    title = record.get("job_title", "")
    source_skills = record.get("required_skills", [])
    if isinstance(source_skills, list):
        source_skills_str = ", ".join(source_skills)
    else:
        source_skills_str = str(source_skills)

    print(f"Testing with Title: {title}")
    print(f"Skills: {source_skills_str}")
    try:
        res = chain.invoke({"title": title, "source_skills": source_skills_str})
        print("Result:", json.dumps(res, indent=2))
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()
