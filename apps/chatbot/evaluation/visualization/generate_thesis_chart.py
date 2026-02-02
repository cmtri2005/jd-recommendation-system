import matplotlib.pyplot as plt
import os
import numpy as np


def generate_thesis_metrics_chart():
    # Metrics verified from evaluation logs
    metrics = {"MRR": 0.82, "Hit Rate@3": 0.87, "NDCG@3": 0.86}

    names = list(metrics.keys())
    values = list(metrics.values())

    # Create output directory
    output_dir = "apps/chatbot/evaluation/results/visualizations"
    os.makedirs(output_dir, exist_ok=True)

    # Setup plot
    fig, ax = plt.subplots(figsize=(8, 6))

    # Create bars
    colors = ["#3498db", "#2ecc71", "#e74c3c"]
    bars = ax.bar(names, values, color=colors, width=0.5)

    # Styling
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("Score", fontsize=12, fontweight="bold")
    ax.set_title(
        "Retrieval Performance Metrics", fontsize=14, fontweight="bold", pad=20
    )
    ax.grid(axis="y", linestyle="--", alpha=0.3)

    # Add values on top of bars
    for bar in bars:
        height = bar.get_height()
        ax.text(
            bar.get_x() + bar.get_width() / 2.0,
            height + 0.02,
            f"{height:.2f}",
            ha="center",
            va="bottom",
            fontsize=11,
            fontweight="bold",
        )

    # Save
    output_path = os.path.join(output_dir, "thesis_retrieval_metrics.png")
    plt.tight_layout()
    plt.savefig(output_path, dpi=300)
    print(f"Chart saved to: {output_path}")


if __name__ == "__main__":
    generate_thesis_metrics_chart()
