"""
Retrieval evaluation metrics utilities.

Provides comprehensive metrics for evaluating retrieval quality:
- MRR (Mean Reciprocal Rank)
- Precision@k
- Recall@k
- NDCG@k (Normalized Discounted Cumulative Gain)
- Hit Rate@k
"""

from typing import List, Dict
import math


def calculate_mrr(results: List[Dict]) -> float:
    """Calculate Mean Reciprocal Rank.

    MRR measures the average position of the first relevant document.
    Higher is better (1.0 = perfect, relevant doc always at position 1).

    Args:
        results: List of dicts with 'ground_truth' and 'contexts' keys

    Returns:
        float: MRR score between 0 and 1

    Example:
        >>> results = [{
        ...     "ground_truth": "doc1",
        ...     "contexts": ["doc1", "doc2", "doc3"]  # Position 1
        ... }]
        >>> calculate_mrr(results)
        1.0
    """
    reciprocal_ranks = []

    for r in results:
        ground_truth = r["ground_truth"]
        contexts = r["contexts"]

        # Find position of first relevant doc
        for i, context in enumerate(contexts):
            if ground_truth in context:
                reciprocal_ranks.append(1 / (i + 1))  # Position is i+1 (1-indexed)
                break
        else:
            # No relevant doc found
            reciprocal_ranks.append(0)

    return sum(reciprocal_ranks) / len(reciprocal_ranks) if reciprocal_ranks else 0


def calculate_precision_at_k(results: List[Dict], k: int) -> float:
    """Calculate Precision@k.

    Precision@k = (# relevant docs in top k) / k
    Measures accuracy of top k results.

    Args:
        results: List of dicts with 'ground_truth' and 'contexts' keys
        k: Number of top results to consider

    Returns:
        float: Precision@k score between 0 and 1
    """
    if k <= 0:
        return 0.0

    precisions = []

    for r in results:
        ground_truth = r["ground_truth"]
        contexts_at_k = r["contexts"][:k]

        # Count relevant docs in top k
        relevant_count = sum(1 for ctx in contexts_at_k if ground_truth in ctx)
        precisions.append(relevant_count / k)

    return sum(precisions) / len(precisions) if precisions else 0


def calculate_recall_at_k(results: List[Dict], k: int) -> float:
    """Calculate Recall@k.

    Recall@k = (# relevant docs retrieved in top k) / (total # relevant docs)
    For our case, we have 1 relevant doc per query.

    Args:
        results: List of dicts with 'ground_truth' and 'contexts' keys
        k: Number of top results to consider

    Returns:
        float: Recall@k score between 0 and 1
    """
    if k <= 0:
        return 0.0

    recalls = []

    for r in results:
        ground_truth = r["ground_truth"]
        contexts_at_k = r["contexts"][:k]

        # For our case: only 1 ground truth per query
        # Recall = 1 if found in top k, else 0
        found = any(ground_truth in ctx for ctx in contexts_at_k)
        recalls.append(1.0 if found else 0.0)

    return sum(recalls) / len(recalls) if recalls else 0


def calculate_ndcg_at_k(results: List[Dict], k: int) -> float:
    """Calculate Normalized Discounted Cumulative Gain at k.

    NDCG@k considers both relevance and position. Relevant docs at
    higher positions get more weight.

    Formula:
    - DCG = sum(relevance_i / log2(position_i + 1))
    - IDCG = DCG of perfect ranking
    - NDCG = DCG / IDCG

    Args:
        results: List of dicts with 'ground_truth' and 'contexts' keys
        k: Number of top results to consider

    Returns:
        float: NDCG@k score between 0 and 1
    """
    if k <= 0:
        return 0.0

    ndcgs = []

    for r in results:
        ground_truth = r["ground_truth"]
        contexts_at_k = r["contexts"][:k]

        # Calculate DCG
        dcg = 0.0
        for i, context in enumerate(contexts_at_k):
            relevance = 1 if ground_truth in context else 0
            # Position is i+1 (1-indexed), log2(i+2) because we want log2(position+1)
            dcg += relevance / math.log2(i + 2)

        # Calculate IDCG (ideal DCG - relevant doc at position 1)
        # For our case with 1 relevant doc: IDCG = 1 / log2(2) = 1.0
        idcg = 1 / math.log2(2)

        # NDCG
        ndcg = dcg / idcg if idcg > 0 else 0
        ndcgs.append(ndcg)

    return sum(ndcgs) / len(ndcgs) if ndcgs else 0


def calculate_hit_rate_at_k(results: List[Dict], k: int) -> Dict:
    """Calculate Hit Rate@k.

    Hit Rate@k = (# queries with relevant doc in top k) / (total # queries)
    Also known as Success Rate or Recall in some contexts.

    Args:
        results: List of dicts with 'ground_truth' and 'contexts' keys
        k: Number of top results to consider

    Returns:
        dict: {
            "hits": int - number of successful queries,
            "total": int - total queries,
            "rate": float - hit rate between 0 and 1
        }
    """
    if k <= 0:
        return {"hits": 0, "total": len(results), "rate": 0.0}

    hits = 0
    for r in results:
        ground_truth = r["ground_truth"]
        contexts_at_k = r["contexts"][:k]

        # Check if ground truth appears in top k
        if any(ground_truth in ctx for ctx in contexts_at_k):
            hits += 1

    total = len(results)
    rate = hits / total if total > 0 else 0

    return {"hits": hits, "total": total, "rate": rate}


def calculate_all_metrics(results: List[Dict], k_values: List[int] = [1, 3, 5]) -> Dict:
    """Calculate all retrieval metrics for given k values.

    Args:
        results: List of evaluation results
        k_values: List of k values to evaluate (default: [1, 3, 5])

    Returns:
        dict: Comprehensive metrics dictionary
    """
    metrics = {
        "mrr": calculate_mrr(results),
        "hit_rate": {},
        "precision": {},
        "recall": {},
        "ndcg": {},
    }

    for k in k_values:
        hit_data = calculate_hit_rate_at_k(results, k)
        metrics["hit_rate"][f"at_{k}"] = hit_data["rate"]
        metrics["precision"][f"at_{k}"] = calculate_precision_at_k(results, k)
        metrics["recall"][f"at_{k}"] = calculate_recall_at_k(results, k)
        metrics["ndcg"][f"at_{k}"] = calculate_ndcg_at_k(results, k)

    return metrics
