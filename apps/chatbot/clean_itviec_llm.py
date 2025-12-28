import os
import json
import logging
import time
import re
from typing import List, Optional
from dotenv import load_dotenv

from langchain_core.prompts import PromptTemplate
from langchain_aws import ChatBedrock
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from pydantic import BaseModel, Field

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load .env
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(os.path.dirname(BASE_DIR))
DOTENV_PATH = os.path.join(ROOT_DIR, ".env")

if os.path.exists(DOTENV_PATH):
    load_dotenv(DOTENV_PATH)
    logger.info(f"Loaded .env from {DOTENV_PATH}")


class JobEnrichment(BaseModel):
    job_level: str = Field(
        description="One of: Intern, Fresher, Junior, Senior, Lead, Manager, Director. Infer mainly from Job Title. Default to 'Junior' if unsure."
    )
    experience_years: float = Field(
        description="Years of experience mentioned in title or skills text. 0.0 if not found."
    )
    skills: List[str] = Field(
        description="Normalized list of technical skills found in the input (e.g. 'React.js' -> 'ReactJS', 'Aws' -> 'AWS')."
    )


def get_llm():
    return ChatBedrock(
        model_id="anthropic.claude-3-haiku-20240307-v1:0",
        model_kwargs={"temperature": 0.0, "max_tokens": 512},
        region_name=os.environ.get("AWS_REGION", "us-east-1"),
    )


parser = JsonOutputParser(pydantic_object=JobEnrichment)
format_instructions = parser.get_format_instructions()

prompt = PromptTemplate(
    template="""Analyze the following job information to extract 3 fields: 
    1. 'job_level': (Intern, Fresher, Junior, Senior, Lead, Manager, Director) based on the Title.
    2. 'experience_years': Number of years required (float).
    3. 'skills': Clean and standard list of technical skills mentioned in the source tags.
    
    Job Title: {title}
    Source Skills/Tags: {source_skills}
    
    Return ONLY valid JSON. Do not include any explanation or conversational text.
    {format_instructions}
    """,
    input_variables=["title", "source_skills"],
    partial_variables={"format_instructions": format_instructions},
)


def extract_json_from_text(text):
    # Try to find JSON block
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return match.group(0)
    return text


def process_job(job_data, llm, retries=3):
    title = job_data.get("job_title", "")
    source_skills = job_data.get("required_skills", [])
    if isinstance(source_skills, list):
        source_skills_str = ", ".join(source_skills)
    else:
        source_skills_str = str(source_skills)

    # Use StrOutputParser to handle chatty models manually
    chain = prompt | llm | StrOutputParser()

    for attempt in range(retries):
        try:
            raw_res = chain.invoke({"title": title, "source_skills": source_skills_str})

            # Clean up response
            json_str = extract_json_from_text(raw_res)

            # Parse JSON
            res = json.loads(json_str)
            return res

        except Exception as e:
            logger.warning(f"Attempt {attempt+1} failed for '{title}': {e}")
            if "ThrottlingException" in str(e):
                time.sleep(2 * (attempt + 1))
                continue
            return None
    return None


def main():
    input_path = os.path.join(
        ROOT_DIR, "apps", "crawler", "data", "raw_itviec", "jobs_details_cleaned.jsonl"
    )
    output_path = os.path.join(
        ROOT_DIR, "apps", "crawler", "data", "itviec_enriched.jsonl"
    )

    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        return

    try:
        llm = get_llm()
    except Exception as e:
        logger.error(f"Failed to initialize Bedrock: {e}")
        return

    # Check processed
    processed_urls = set()
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        j = json.loads(line)
                        processed_urls.add(j.get("url"))
                    except:
                        pass

    data = []
    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    data.append(json.loads(line))
                except:
                    pass

    logger.info(f"Total records: {len(data)}. Already processed: {len(processed_urls)}")

    with open(output_path, "a", encoding="utf-8") as f_out:
        for i, item in enumerate(data):
            if item.get("url") in processed_urls:
                continue

            logger.info(f"Processing {i+1}/{len(data)}: {item.get('job_title')}")

            extracted = process_job(item, llm)

            if extracted:
                item["normalized_level"] = extracted.get("job_level")
                item["normalized_exp_years"] = extracted.get("experience_years")
                item["normalized_skills"] = extracted.get("skills")
            else:
                # Fallback
                item["normalized_level"] = None
                item["normalized_exp_years"] = 0.0
                item["normalized_skills"] = item.get("required_skills", [])

            f_out.write(json.dumps(item, ensure_ascii=False) + "\n")
            f_out.flush()

            # Minor delay
            time.sleep(0.1)

    logger.info("Done enrichment.")


if __name__ == "__main__":
    main()
