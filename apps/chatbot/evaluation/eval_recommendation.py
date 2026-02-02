import sys
import os
import json
import time
import logging
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from core.agents.evaluation_agent import EvaluationAgent
from core.factories.llm_factory import LLMFactory
from config.config import config
from schemas.evaluation import EvaluationResult
from evaluation.utils.rate_limiter import RateLimiter, RateLimitConfig, load_config

load_dotenv()
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
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


def evaluate_with_retry(
    agent: EvaluationAgent,
    rate_limiter: RateLimiter,
    resume: str,
    jd: str,
    eval_type: str,
) -> Optional[EvaluationResult]:
    """Evaluate with rate limiting and retry logic."""

    def _evaluate():
        return agent.evaluate(resume, jd)

    try:
        result = rate_limiter.with_retry(_evaluate)
        logger.info(
            f"{eval_type} eval: {result.total_score}/100 "
            f"(Hard Skills: {result.score_breakdown.hard_skills_score}/30)"
        )
        return result
    except Exception as e:
        logger.error(f"Error evaluating {eval_type} after all retries: {e}")
        return None


def calculate_eta(start_time: float, processed: int, total: int) -> str:
    """Calculate estimated time remaining."""
    if processed == 0:
        return "calculating..."

    elapsed = time.time() - start_time
    rate = processed / elapsed
    remaining = total - processed
    eta_seconds = remaining / rate if rate > 0 else 0

    eta_delta = timedelta(seconds=int(eta_seconds))
    return str(eta_delta)


def main():
    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Run recommendation evaluation with rate limiting"
    )
    parser.add_argument(
        "--config", type=str, default=None, help="Path to batch configuration JSON file"
    )
    parser.add_argument(
        "--batch-size", type=int, default=None, help="Override batch size"
    )
    parser.add_argument(
        "--batch-delay",
        type=float,
        default=None,
        help="Override batch delay in seconds",
    )
    parser.add_argument(
        "--item-delay", type=float, default=None, help="Override item delay in seconds"
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=None,
        help="Maximum number of items to process (for testing)",
    )
    args = parser.parse_args()

    # Load configuration
    base_dir = os.path.dirname(__file__)
    if args.config:
        config_path = args.config
    else:
        config_path = os.path.join(base_dir, "batch_config.json")

    rate_config = load_config(config_path)

    # Override with command-line arguments
    if args.batch_size is not None:
        rate_config.batch_size = args.batch_size
    if args.batch_delay is not None:
        rate_config.batch_delay = args.batch_delay
    if args.item_delay is not None:
        rate_config.item_delay = args.item_delay

    logger.info(
        f"Using configuration: batch_size={rate_config.batch_size}, "
        f"batch_delay={rate_config.batch_delay}s, "
        f"item_delay={rate_config.item_delay}s"
    )

    # Initialize rate limiter
    rate_limiter = RateLimiter(rate_config)

    # AWS BEDROCK
    model_name = config.BEDROCK_LLM_MODEL
    model_region = config.BEDROCK_MODEL_REGION

    llm = LLMFactory.create_llm(
        llm_provider=LLMFactory.Provider.BEDROCK,
        config=LLMFactory.LLMConfig(model_name=model_name, model_region=model_region),
    )

    agent = EvaluationAgent("eval_tester", llm, tools=[])

    data_path = os.path.join(base_dir, "dataset", "golden_dataset.json")
    cache_path = os.path.join(base_dir, "cache", "recommendation_cache.json")

    if not os.path.exists(data_path):
        logger.error("Golden dataset not found.")
        return

    dataset = load_golden_dataset(data_path)

    # Limit dataset size if requested
    if args.max_items:
        dataset = dataset[: args.max_items]
        logger.info(f"Limited dataset to {args.max_items} items for testing")

    cache = load_cache(cache_path)
    logger.info(f"Loaded {len(cache)} cached results.")

    results = []

    print("\n" + "=" * 60)
    print("🚀 RECOMMENDATION EVALUATION - BATCH MODE")
    print("=" * 60)
    print(f"Total items: {len(dataset)}")
    print(f"Cached items: {len(cache)}")
    print(
        f"Items to process: {len(dataset) - len([d for d in dataset if d['job_title'] in cache])}"
    )
    print("=" * 60 + "\n")

    BATCH_SIZE = rate_config.batch_size
    BATCH_DELAY = rate_config.batch_delay
    ITEM_DELAY = rate_config.item_delay

    processed_count = 0
    start_time = time.time()

    for i in range(0, len(dataset), BATCH_SIZE):
        batch = dataset[i : i + BATCH_SIZE]

        # Calculate progress
        items_processed = i
        progress_pct = (items_processed / len(dataset)) * 100
        eta = calculate_eta(start_time, items_processed, len(dataset))

        print(f"\n{'='*60}")
        print(
            f"📦 Batch {i//BATCH_SIZE + 1} | Items {i+1}-{min(i+BATCH_SIZE, len(dataset))} / {len(dataset)}"
        )
        print(f"📊 Progress: {progress_pct:.1f}% | ETA: {eta}")
        print(f"{'='*60}")

        batch_modified = False

        for item in batch:
            job_title = item["job_title"]

            # Check Cache
            if job_title in cache:
                logger.info(f"✓ Skipping '{job_title}' (cached)")
                results.append(cache[job_title])
                continue

            processed_count += 1
            jd = item["jd_text"]

            print(f"\n🔄 Processing: {job_title}")

            # Test Positive with retry
            print(f"  ➤ Testing Positive Match...")
            pos_result = evaluate_with_retry(
                agent, rate_limiter, item["positive_resume"], jd, "Positive"
            )

            # Delay between positive and negative
            time.sleep(ITEM_DELAY)

            # Test Negative with retry
            print(f"  ➤ Testing Negative Match...")
            neg_result = evaluate_with_retry(
                agent, rate_limiter, item["negative_resume"], jd, "Negative"
            )

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

            status = "✅ PASS" if result_entry["success"] else "❌ FAIL"
            print(
                f"  ✓ Result: Pos={result_entry['pos_score']}, "
                f"Neg={result_entry['neg_score']} | {status}"
            )
            time.sleep(ITEM_DELAY)

        # Save cache after each batch if there were changes
        if batch_modified:
            save_cache(cache_path, cache)
            logger.info(f"💾 Cache saved ({len(cache)} items)")

        # Delay between batches (only if we actually processed something in this batch)
        if batch_modified and (i + BATCH_SIZE < len(dataset)):
            print(f"\n⏸️  Batch delay: waiting {BATCH_DELAY}s to prevent rate limits...")
            time.sleep(BATCH_DELAY)

    # Final statistics
    total_time = time.time() - start_time
    stats = rate_limiter.get_stats()

    print("\n" + "=" * 60)
    print("📈 RATE LIMITER STATISTICS")
    print("=" * 60)
    print(f"Total API requests: {stats['total_requests']}")
    print(f"Failed requests: {stats['failed_requests']}")
    print(f"Rate limit hits: {stats['rate_limit_hits']}")
    print(f"Success rate: {stats['success_rate']}%")
    print(f"Total wait time: {stats['total_wait_time']:.1f}s")
    print(f"Total execution time: {total_time:.1f}s")
    print("=" * 60)

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
