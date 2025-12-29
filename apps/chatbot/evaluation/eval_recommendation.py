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
from schema.evaluation import EvaluationResult

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_golden_dataset(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


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
            pos_result = None
            try:
                pos_result = agent.evaluate(item["positive_resume"], jd)
                logger.info(
                    f"Positive eval: {pos_result.total_score}/100 "
                    f"(Hard Skills: {pos_result.score_breakdown.hard_skills_score}/30)"
                )
            except Exception as e:
                logger.error(f"Error evaluating positive: {e}")
                pos_result = None

            # Delay between positive and negative
            time.sleep(2)

            # Test Negative
            print(f"Testing Negative Match for {job_title}...")
            neg_result = None
            try:
                neg_result = agent.evaluate(item["negative_resume"], jd)
                logger.info(
                    f"Negative eval: {neg_result.total_score}/100 "
                    f"(Hard Skills: {neg_result.score_breakdown.hard_skills_score}/30)"
                )
            except Exception as e:
                logger.error(f"Error evaluating negative: {e}")
                neg_result = None

            # Calculate success
            if pos_result and neg_result:
                pos_score = pos_result.total_score
                neg_score = neg_result.total_score
                success = pos_score > 70 and neg_score < 70

                result_entry = {
                    "job": job_title,
                    "pos_score": pos_score,
                    "neg_score": neg_score,
                    "success": success,
                    "pos_breakdown": pos_result.score_breakdown.model_dump(),
                    "neg_breakdown": neg_result.score_breakdown.model_dump(),
                    "pos_recommendation": pos_result.recommendation,
                    "neg_recommendation": neg_result.recommendation,
                    "missing_skills": [
                        skill.model_dump() for skill in pos_result.missing_hard_skills
                    ],
                    "pos_summary": pos_result.summary,
                    "neg_summary": neg_result.summary,
                }
            else:
                # Fallback for errors
                result_entry = {
                    "job": job_title,
                    "pos_score": pos_result.total_score if pos_result else 0,
                    "neg_score": neg_result.total_score if neg_result else 0,
                    "success": False,
                    "error": "Evaluation failed",
                }

            results.append(result_entry)
            cache[job_title] = result_entry
            batch_modified = True

            print(
                f"   -> Result: Positive={result_entry['pos_score']}, "
                f"Negative={result_entry['neg_score']} | Pass: {result_entry['success']}"
            )

        # Save cache after each batch if there were changes
        if batch_modified:
            save_cache(cache_path, cache)

        # Delay between batches (only if we actually processed something in this batch)
        if batch_modified and (i + BATCH_SIZE < len(dataset)):
            print(f"Sleeping {BATCH_DELAY}s to prevent throttling...")
            time.sleep(BATCH_DELAY)

    # Summary
    pass_count = sum(1 for r in results if r.get("success", False))
    print("\n" + "=" * 30)
    print(
        f"Recommendation Accuracy: {pass_count}/{len(results)} "
        f"({pass_count/len(results)*100:.1f}%)"
    )
    print("=" * 30)

    # Detailed Analysis
    print("\n📊 Detailed Analysis:")

    # Score distribution
    pos_scores = [r["pos_score"] for r in results if "pos_score" in r]
    neg_scores = [r["neg_score"] for r in results if "neg_score" in r]

    if pos_scores:
        print(
            f"\nPositive Scores: Avg={sum(pos_scores)/len(pos_scores):.1f}, "
            f"Min={min(pos_scores)}, Max={max(pos_scores)}"
        )
    if neg_scores:
        print(
            f"Negative Scores: Avg={sum(neg_scores)/len(neg_scores):.1f}, "
            f"Min={min(neg_scores)}, Max={max(neg_scores)}"
        )

    # Most common missing skills
    all_missing_skills = []
    for r in results:
        if "missing_skills" in r:
            all_missing_skills.extend([s["skill_name"] for s in r["missing_skills"]])

    if all_missing_skills:
        from collections import Counter

        skill_counts = Counter(all_missing_skills)
        print("\n🎯 Top 5 Most Common Missing Skills:")
        for skill, count in skill_counts.most_common(5):
            print(f"  - {skill}: {count} times")

    # Save Report
    output_path = os.path.join(base_dir, "results", "evaluation_report.json")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    print(f"\n✅ Full report saved to {output_path}")


if __name__ == "__main__":
    main()


if __name__ == "__main__":
    main()
