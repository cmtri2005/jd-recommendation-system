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
        os.path.dirname(__file__), "..", "dataset", "golden_dataset.json"
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

    try:
        print("Calculating exact match recall (Simplified)...")
        hits = 0
        for r in results:
            if r["ground_truth"] in r["contexts"]:
                hits += 1

        print(
            f"Exact Hit Rate @ 3: {hits}/{len(results)} ({hits/len(results)*100:.2f}%)"
        )

    except Exception as e:
        print(f"Ragas evaluation failed: {e}")

    # 6. Save results
    output_dir = os.path.join(os.path.dirname(__file__), "results")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, "retrieval_evaluation.json")

    output_data = {
        "metrics": {
            "exact_hit_rate": (
                f"{hits}/{len(results)} ({hits/len(results)*100:.2f}%)"
                if results
                else "0%"
            )
        },
        "details": results,
    }

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"Evaluation results saved to {output_path}")


if __name__ == "__main__":
    main()
