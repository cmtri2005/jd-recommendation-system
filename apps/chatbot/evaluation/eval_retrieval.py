import sys
import os
import json
import logging
from typing import List, Dict
from dotenv import load_dotenv

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

os.environ["DATASET_NAME"] = "jd-eval-test"

from config.config import config
from core.agents.retrieval_agent import RetrievalAgent
from core.factories.llm_factory import LLMFactory
from langchain_core.documents import Document
from ragas import evaluate
from ragas.metrics import context_precision, context_recall
from datasets import Dataset
from evaluation.metrics_utils import calculate_all_metrics, calculate_hit_rate_at_k

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_golden_dataset(path: str) -> List[Dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ingest_test_data(agent: RetrievalAgent, dataset: List[Dict]):
    """Ingest the JDs from our golden dataset into the test vector store."""
    documents = []
    for item in dataset:
        doc = Document(
            page_content=item["jd_text"],
            metadata={"source": "golden_dataset", "title": item["job_title"]},
        )
        documents.append(doc)

    # Add to vectorstore
    ids = agent.vectorstore.add_documents(documents)
    logger.info(f"Ingested {len(ids)} documents into test collection.")


def prepare_ragas_dataset(results: List[Dict]) -> Dataset:
    """Convert our results to Ragas compatible dataset."""
    valid_results = [r for r in results if r is not None]  # Filter out failures
    data = {
        "question": [r["question"] for r in valid_results],
        "contexts": [r["contexts"] for r in valid_results],
        "ground_truth": [r["ground_truth"] for r in valid_results],
        "answer": ["N/A"] * len(valid_results),
    }
    return Dataset.from_dict(data)


def main():
    # 1. Setup
    model_name = config.BEDROCK_LLM_MODEL
    model_region = config.BEDROCK_MODEL_REGION

    llm = LLMFactory.create_llm(
        llm_provider=LLMFactory.Provider.BEDROCK,
        config=LLMFactory.LLMConfig(model_name=model_name, model_region=model_region),
    )
    agent = RetrievalAgent("retrieval_eval", llm, tools=[])

    # 2. Load Data
    data_path = os.path.join(
        os.path.dirname(__file__), "dataset", "golden_dataset.json"
    )
    if not os.path.exists(data_path):
        print("Golden dataset not found. Run generate_dataset.py first.")
        return

    dataset = load_golden_dataset(data_path)

    # 3. Ingest Data
    try:
        agent.vectorstore.delete_collection()
    except:
        pass

    agent = RetrievalAgent("retrieval_eval", llm, tools=[])
    ingest_test_data(agent, dataset)

    # 4. Run Retrieval
    results = []
    print("Running retrieval evaluation...")

    for item in dataset:
        # Use Positive Resume
        query = item["positive_resume"]
        ground_truth = item["jd_text"]

        try:
            docs = agent.vectorstore.similarity_search(query, k=3)
            retrieved_contexts = [d.page_content for d in docs]

            results.append(
                {
                    "question": query,
                    "contexts": retrieved_contexts,
                    "ground_truth": ground_truth,
                }
            )
        except Exception as e:
            logger.error(f"Error processing item: {e}")

    # 5. Evaluate with Ragas
    if not results:
        print("No results to evaluate.")
        return

    ragas_ds = prepare_ragas_dataset(results)

    # Calculate comprehensive metrics
    print("\n" + "=" * 60)
    print("📊 RETRIEVAL EVALUATION METRICS")
    print("=" * 60)

    try:
        # Calculate all metrics at once
        metrics = calculate_all_metrics(results, k_values=[1, 3, 5])

        # Display Hit Rate @ k
        print("\n🎯 Hit Rate @ k (Success Rate):")
        for k in [1, 3, 5]:
            rate = metrics["hit_rate"][f"at_{k}"]
            hit_data = calculate_hit_rate_at_k(results, k)
            print(
                f"  - Hit Rate @ {k}: {hit_data['hits']}/{hit_data['total']} "
                f"({rate*100:.2f}%)"
            )

        # Display MRR
        print(f"\n📍 Mean Reciprocal Rank (MRR): {metrics['mrr']:.4f}")
        print("   (Higher = relevant docs appear earlier)")

        # Display Precision @ k
        print("\n🎯 Precision @ k (Accuracy of top k):")
        for k in [1, 3, 5]:
            precision = metrics["precision"][f"at_{k}"]
            print(f"  - P@{k}: {precision:.4f}")

        # Display Recall @ k
        print("\n📦 Recall @ k (Coverage in top k):")
        for k in [1, 3, 5]:
            recall = metrics["recall"][f"at_{k}"]
            print(f"  - R@{k}: {recall:.4f}")

        # Display NDCG @ k
        print("\n⭐ NDCG @ k (Quality weighted by ranking):")
        for k in [1, 3, 5]:
            ndcg = metrics["ndcg"][f"at_{k}"]
            print(f"  - NDCG@{k}: {ndcg:.4f}")

        print("\n" + "=" * 60)

        # Industry benchmarks comparison
        print("\n📈 Benchmark Comparison:")
        if metrics["mrr"] >= 0.6:
            print("  ✅ MRR: Good (>= 0.6)")
        else:
            print(f"  ⚠️  MRR: Needs improvement (< 0.6)")

        if (
            metrics["hit_rate"]["at_10" if "at_10" in metrics["hit_rate"] else "at_5"]
            >= 0.8
        ):
            print("  ✅ Hit Rate: Good (>= 0.8)")
        elif metrics["hit_rate"]["at_5"] >= 0.7:
            print("  ⚠️  Hit Rate: Fair (>= 0.7)")
        else:
            print("  ❌ Hit Rate: Needs improvement (< 0.7)")

    except Exception as e:
        logger.error(f"Metrics calculation failed: {e}")
        import traceback

        traceback.print_exc()
        # Fallback to basic hit rate
        metrics = {"error": str(e)}

    # 6. Save results
    output_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "retrieval_evaluation.json")

    # Prepare comprehensive output
    output_data = {
        "metrics": (
            metrics
            if "error" not in metrics
            else {
                "error": metrics.get("error"),
                "note": "Metrics calculation failed, see error above",
            }
        ),
        "summary": {
            "total_queries": len(results),
            "dataset_used": "golden_dataset.json",
            "retrieval_k": 3,
            "embedding_model": (
                config.BEDROCK_EMBEDDING_MODEL
                if hasattr(config, "BEDROCK_EMBEDDING_MODEL")
                else "default"
            ),
        },
        "details": results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Evaluation results saved to {output_path}")


if __name__ == "__main__":
    main()
