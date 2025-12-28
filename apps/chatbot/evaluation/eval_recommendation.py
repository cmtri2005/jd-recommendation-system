import sys
import os
import json
import time
import logging
from typing import List, Dict
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.agents.evaluation_agent import EvaluationAgent
from core.factories.llm_factory import LLMFactory
from config.config import config

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_golden_dataset(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_score(response_text: str) -> int:
    """Heuristic to extract score from agent output."""
    try:
        # Simple extraction logic: look for "Total score" line
        lines = response_text.split("\n")
        for line in lines:
            if "total score" in line.lower():
                # Extract digits
                digits = [int(s) for s in line.split() if s.isdigit()]
                if digits:
                    return digits[0]
        # Fallback: naive search for any 2digit number
        import re

        matches = re.findall(r"\b\d{2,3}\b", response_text)
        if matches:
            return int(matches[0])
    except:
        pass
    return 0


def load_cache(path: str) -> Dict[str, Dict]:
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_cache(path: str, cache: Dict[str, Dict]):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(cache, f, indent=2, ensure_ascii=False)


def main():
    # AWS BEDROCK
    model_name = config.BEDROCK_LLM_MODEL
    model_region = config.BEDROCK_MODEL_REGION

    llm = LLMFactory.create_llm(
        llm_provider=LLMFactory.Provider.BEDROCK,
        config=LLMFactory.LLMConfig(model_name=model_name, model_region=model_region),
    )

    agent = EvaluationAgent("eval_tester", llm, tools=[])

    base_dir = os.path.dirname(__file__)
    data_path = os.path.join(base_dir, "..", "dataset", "golden_dataset.json")
    cache_path = os.path.join(base_dir, "cache", "recommendation_cache.json")

    if not os.path.exists(data_path):
        print("Golden dataset not found.")
        return

    dataset = load_golden_dataset(data_path)
    cache = load_cache(cache_path)
    print(f"Loaded {len(cache)} cached results.")

    results = []

    print("Running recommendation evaluation...")

    BATCH_SIZE = 5
    BATCH_DELAY = 10  # seconds

    processed_count = 0

    for i in range(0, len(dataset), BATCH_SIZE):
        batch = dataset[i : i + BATCH_SIZE]
        print(f"\nExample {i+1}-{min(i+BATCH_SIZE, len(dataset))} / {len(dataset)}")

        batch_modified = False

        for item in batch:
            job_title = item["job_title"]

            # Check Cache
            if job_title in cache:
                print(f"Skipping {job_title} (Found in cache)")
                results.append(cache[job_title])
                continue

            processed_count += 1
            jd = item["jd_text"]

            # Test Positive
            print(f"Testing Positive Match for {job_title}...")
            pos_score = 0
            try:
                pos_res = agent.evaluate(item["positive_resume"], jd)
                pos_score = extract_score(pos_res)
            except Exception as e:
                print(f"Error evaluating positive: {e}")

            # Delay between positive and negative
            time.sleep(2)

            # Test Negative
            print(f"Testing Negative Match for {job_title}...")
            neg_score = 0
            try:
                neg_res = agent.evaluate(item["negative_resume"], jd)
                neg_score = extract_score(neg_res)
            except Exception as e:
                print(f"Error evaluating negative: {e}")

            success = pos_score > 70 and neg_score < 70

            result_entry = {
                "job": job_title,
                "pos_score": pos_score,
                "neg_score": neg_score,
                "success": success,
            }

            results.append(result_entry)
            cache[job_title] = result_entry
            batch_modified = True

            print(
                f"   -> Result: Positive={pos_score}, Negative={neg_score} | Pass: {success}"
            )

        # Save cache after each batch if there were changes
        if batch_modified:
            save_cache(cache_path, cache)

        # Delay between batches (only if we actually processed something in this batch)
        if batch_modified and (i + BATCH_SIZE < len(dataset)):
            print(f"Sleeping {BATCH_DELAY}s to prevent throttling...")
            time.sleep(BATCH_DELAY)

    # Summary
    pass_count = sum(1 for r in results if r["success"])
    print("\n" + "=" * 30)
    print(
        f"Recommendation Accuracy: {pass_count}/{len(results)} ({pass_count/len(results)*100:.1f}%)"
    )
    print("=" * 30)

    # Save Report
    report_path = os.path.join(
        os.path.dirname(__file__), "..", "evaluation_report.json"
    )
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"Full report saved to {report_path}")


if __name__ == "__main__":
    main()
