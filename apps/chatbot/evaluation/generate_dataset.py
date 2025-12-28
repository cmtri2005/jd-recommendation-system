import sys
import os
import json
import time
import random
from typing import List, Dict
from dotenv import load_dotenv
from config.config import config

# Add parent directory to path to allow importing core modules
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.factories.llm_factory import LLMFactory
from langchain_core.prompts import ChatPromptTemplate

load_dotenv()


def load_jds(limit: int = 100) -> List[Dict]:
    """Load JDs from the crawler output."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.abspath(
        os.path.join(base_dir, "..", "..", "crawler", "data", "jobs_raw.jsonl")
    )

    jds = []
    if not os.path.exists(data_path):
        print(f"File not found: {data_path}")
        return []

    with open(data_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                try:
                    data = json.loads(line)
                    if data.get("job_description"):
                        jds.append(data)
                except:
                    continue

    # Shuffle and pick random
    random.shuffle(jds)
    return jds[:limit]


def generate_resume(llm, jd_text: str, is_positive: bool) -> str:
    """Generate a synthetic resume based on JD."""

    if is_positive:
        instruction = "Create a PERFECT MATCH resume for this job description. Include all required hard skills, soft skills, and relevant experience. Format it as a plain text resume."
    else:
        instruction = "Create a BAD MATCH resume for this job description. The candidate should be from a completely different field or lack key skills (e.g., if JD is for detailed Java backend, make resume for a junior Marketing intern or Python Data Scientist with no Java knowledge). Format it as a plain text resume."

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an expert HR assistant helping to generate synthetic test data.",
            ),
            ("human", f"{instruction}\n\nJOB DESCRIPTION:\n{jd_text}"),
        ]
    )

    chain = prompt | llm
    result = chain.invoke({})
    return result.content


def main():
    print("Initializing LLM...")
    model_name = config.BEDROCK_LLM_MODEL
    model_region = config.BEDROCK_MODEL_REGION

    llm = LLMFactory.create_llm(
        llm_provider=LLMFactory.Provider.BEDROCK,
        config=LLMFactory.LLMConfig(model_name=model_name, model_region=model_region),
    )

    print("Loading JDs...")
    jds = load_jds(limit=100)
    print(f"Loaded {len(jds)} JDs.")

    dataset = []

    for i, jd_item in enumerate(jds):
        jd_text = jd_item.get("job_description", "")
        job_title = jd_item.get("job_title", "Unknown")

        print(f"[{i+1}/{len(jds)}] Generating for {job_title}...")

        try:
            # Generate Positive Sample
            positive_resume = generate_resume(llm, jd_text, is_positive=True)

            # Generate Negative Sample
            negative_resume = generate_resume(llm, jd_text, is_positive=False)

            dataset.append(
                {
                    "job_title": job_title,
                    "jd_text": jd_text,
                    "positive_resume": positive_resume,
                    "negative_resume": negative_resume,
                }
            )
        except Exception as e:
            print(f"Error generating for {job_title}: {e}")

    # Save dataset
    output_dir = os.path.join(os.path.dirname(__file__), "..", "dataset")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "golden_dataset.json")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"Saved golden dataset to {output_path}")


if __name__ == "__main__":
    main()
