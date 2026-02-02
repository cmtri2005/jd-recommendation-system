"""
Visualize retrieval evaluation metrics.
"""

import json
import os
import matplotlib.pyplot as plt
import numpy as np


def load_results(path: str):
    """Load evaluation results."""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def create_metrics_comparison_chart(metrics: dict, output_dir: str):
    """Create comparison chart for Precision, Recall, NDCG across k values."""
    k_values = [1, 3, 5]

    precision = [metrics["precision"][f"at_{k}"] for k in k_values]
    recall = [metrics["recall"][f"at_{k}"] for k in k_values]
    ndcg = [metrics["ndcg"][f"at_{k}"] for k in k_values]

    x = np.arange(len(k_values))
    width = 0.25

    fig, ax = plt.subplots(figsize=(10, 6))

    bars1 = ax.bar(x - width, precision, width, label="Precision@k", color="#3498db")
    bars2 = ax.bar(x, recall, width, label="Recall@k", color="#2ecc71")
    bars3 = ax.bar(x + width, ndcg, width, label="NDCG@k", color="#f39c12")

    ax.set_xlabel("k (Top k results)", fontsize=12, fontweight="bold")
    ax.set_ylabel("Score", fontsize=12, fontweight="bold")
    ax.set_title(
        "Retrieval Metrics Comparison (Precision, Recall, NDCG)",
        fontsize=14,
        fontweight="bold",
        pad=20,
    )
    ax.set_xticks(x)
    ax.set_xticklabels([f"k={k}" for k in k_values])
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.set_ylim(0, 1.0)

    # Add value labels on bars
    for bars in [bars1, bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                height,
                f"{height:.3f}",
                ha="center",
                va="bottom",
                fontsize=9,
            )

    plt.tight_layout()
    plt.savefig(
        os.path.join(output_dir, "metrics_comparison.png"), dpi=300, bbox_inches="tight"
    )
    plt.close()
    print("✅ Created: metrics_comparison.png")


def create_hit_rate_chart(metrics: dict, output_dir: str):
    """Create hit rate progression chart."""
    k_values = [1, 3, 5]
    hit_rates = [metrics["hit_rate"][f"at_{k}"] * 100 for k in k_values]

    fig, ax = plt.subplots(figsize=(10, 6))

    bars = ax.bar(
        [f"k={k}" for k in k_values],
        hit_rates,
        color=["#e74c3c", "#3498db", "#2ecc71"],
        edgecolor="black",
        linewidth=1.5,
    )

    ax.set_xlabel("Top k Results", fontsize=12, fontweight="bold")
    ax.set_ylabel("Hit Rate (%)", fontsize=12, fontweight="bold")
    ax.set_title("Hit Rate @ k (Success Rate)", fontsize=14, fontweight="bold", pad=20)
    ax.grid(axis="y", alpha=0.3, linestyle="--")
    ax.set_ylim(0, 100)

    # Add benchmark line
    ax.axhline(
        y=80,
        color="green",
        linestyle="--",
        linewidth=2,
        label="Good Benchmark (80%)",
        alpha=0.7,
    )
    ax.legend(loc="lower right", fontsize=10)

    # Add value labels
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height,
            f"{height:.1f}%",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "hit_rate.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print("✅ Created: hit_rate.png")


def create_summary_dashboard(metrics: dict, summary: dict, output_dir: str):
    """Create summary dashboard with key metrics."""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle(
        "Retrieval System Performance Dashboard", fontsize=16, fontweight="bold", y=0.98
    )

    # 1. MRR Gauge
    ax1 = axes[0, 0]
    mrr = metrics["mrr"]
    colors = ["#e74c3c" if mrr < 0.4 else "#f39c12" if mrr < 0.6 else "#2ecc71"]
    ax1.barh(["MRR"], [mrr], color=colors[0], height=0.3)
    ax1.set_xlim(0, 1.0)
    ax1.set_xlabel("Score", fontweight="bold")
    ax1.set_title("Mean Reciprocal Rank (MRR)", fontweight="bold", pad=10)
    ax1.text(
        mrr / 2,
        0,
        f"{mrr:.4f}",
        ha="center",
        va="center",
        fontsize=14,
        fontweight="bold",
        color="white",
    )
    ax1.axvline(x=0.6, color="green", linestyle="--", linewidth=2, alpha=0.5)
    ax1.grid(axis="x", alpha=0.3)

    # 2. Hit Rate @ k
    ax2 = axes[0, 1]
    k_vals = [1, 3, 5]
    hit_rates = [metrics["hit_rate"][f"at_{k}"] for k in k_vals]
    ax2.plot(k_vals, hit_rates, marker="o", linewidth=2, markersize=10, color="#3498db")
    ax2.fill_between(k_vals, hit_rates, alpha=0.3, color="#3498db")
    ax2.set_xlabel("k", fontweight="bold")
    ax2.set_ylabel("Hit Rate", fontweight="bold")
    ax2.set_title("Hit Rate Progression", fontweight="bold", pad=10)
    ax2.set_xticks(k_vals)
    ax2.set_ylim(0, 1.0)
    ax2.grid(True, alpha=0.3)
    for i, (k, rate) in enumerate(zip(k_vals, hit_rates)):
        ax2.text(k, rate + 0.02, f"{rate:.2f}", ha="center", fontweight="bold")

    # 3. Precision vs Recall
    ax3 = axes[1, 0]
    precision = [metrics["precision"][f"at_{k}"] for k in k_vals]
    recall = [metrics["recall"][f"at_{k}"] for k in k_vals]

    x = np.arange(len(k_vals))
    width = 0.35
    ax3.bar(x - width / 2, precision, width, label="Precision", color="#9b59b6")
    ax3.bar(x + width / 2, recall, width, label="Recall", color="#1abc9c")
    ax3.set_xlabel("k", fontweight="bold")
    ax3.set_ylabel("Score", fontweight="bold")
    ax3.set_title("Precision vs Recall @ k", fontweight="bold", pad=10)
    ax3.set_xticks(x)
    ax3.set_xticklabels(k_vals)
    ax3.legend()
    ax3.set_ylim(0, 1.0)
    ax3.grid(axis="y", alpha=0.3)

    # 4. Summary Stats
    ax4 = axes[1, 1]
    ax4.axis("off")

    summary_text = f"""
    📊 EVALUATION SUMMARY
    
    Total Queries: {summary.get('total_queries', 'N/A')}
    Dataset: {summary.get('dataset_used', 'N/A')}
    Retrieval k: {summary.get('retrieval_k', 'N/A')}
    
    🏆 KEY METRICS:
    • MRR: {mrr:.4f}
    • Hit Rate @ 3: {hit_rates[1]:.2%}
    • NDCG @ 3: {metrics['ndcg']['at_3']:.4f}
    
    ✅ BENCHMARKS:
    • MRR: {'PASS ✓' if mrr >= 0.6 else 'FAIL ✗'}
    • Hit Rate: {'PASS ✓' if hit_rates[1] >= 0.8 else 'FAIR' if hit_rates[1] >= 0.7 else 'FAIL ✗'}
    """

    ax4.text(
        0.1,
        0.5,
        summary_text,
        fontsize=11,
        verticalalignment="center",
        fontfamily="monospace",
        bbox=dict(boxstyle="round", facecolor="wheat", alpha=0.3),
    )

    plt.tight_layout()
    plt.savefig(os.path.join(output_dir, "dashboard.png"), dpi=300, bbox_inches="tight")
    plt.close()
    print("✅ Created: dashboard.png")


def main():
    # Load results
    results_path = os.path.join(
        os.path.dirname(__file__), "..", "results", "retrieval_evaluation.json"
    )

    if not os.path.exists(results_path):
        print(f"❌ Results file not found: {results_path}")
        return

    data = load_results(results_path)
    metrics = data.get("metrics", {})
    summary = data.get("summary", {})

    if "error" in metrics:
        print(f"❌ Cannot visualize - metrics contain errors: {metrics['error']}")
        return

    # Create output directory
    output_dir = os.path.join(
        os.path.dirname(__file__), "..", "results", "visualizations"
    )
    os.makedirs(output_dir, exist_ok=True)

    print("\n🎨 Generating visualizations...")
    print("=" * 60)

    # Generate charts
    create_hit_rate_chart(metrics, output_dir)
    create_metrics_comparison_chart(metrics, output_dir)
    create_summary_dashboard(metrics, summary, output_dir)

    print("=" * 60)
    print(f"\n✅ All visualizations saved to: {output_dir}")
    print("\n📁 Generated files:")
    print("  1. hit_rate.png - Hit rate progression")
    print("  2. metrics_comparison.png - Precision/Recall/NDCG comparison")
    print("  3. dashboard.png - Complete performance dashboard")


if __name__ == "__main__":
    main()
