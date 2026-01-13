import json
import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
from typing import List, Dict

# Set style
sns.set_theme(style="whitegrid")
plt.rcParams["figure.figsize"] = [10, 6]
plt.rcParams["font.size"] = 12


def load_json(path: str) -> Dict:
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def ensure_dir(path: str):
    if not os.path.exists(path):
        os.makedirs(path)


def visualize_retrieval(data: Dict, output_dir: str):
    print("Visualizing Retrieval Evaluation...")

    if "metrics" not in data or "hit_rate" not in data["metrics"]:
        print("Invalid retrieval data structure.")
        return

    metrics = data["metrics"]
    hit_rate = metrics["hit_rate"]

    # 1. Hit Rate Bar Chart
    k_values = [k.replace("at_", "") for k in hit_rate.keys()]
    scores = [v for v in hit_rate.values()]

    plt.figure()
    ax = sns.barplot(x=k_values, y=scores, palette="viridis")
    ax.set_title("Retrieval Hit Rate @ K")
    ax.set_xlabel("K")
    ax.set_ylabel("Hit Rate")
    ax.set_ylim(0, 1.1)

    for i, v in enumerate(scores):
        ax.text(i, v + 0.01, f"{v:.2f}", ha="center")

    plt.savefig(os.path.join(output_dir, "retrieval_hit_rate.png"))
    plt.close()

    print(f"Saved retrieval_hit_rate.png to {output_dir}")


def visualize_recommendation(data: List[Dict], output_dir: str):
    print("Visualizing Recommendation Evaluation...")

    if not data:
        print("No recommendation data found.")
        return

    df = pd.DataFrame(data)

    # Filter valid rows
    if "pos_score" not in df.columns or "neg_score" not in df.columns:
        print("Data is missing score columns.")
        return

    # 1. Score Distribution (Histogram)
    plt.figure()
    sns.histplot(
        df["pos_score"], color="green", label="Positive Resume", kde=True, alpha=0.6
    )
    sns.histplot(
        df["neg_score"], color="red", label="Negative Resume", kde=True, alpha=0.6
    )
    plt.title("Score Distribution: Positive vs Negative Resumes")
    plt.xlabel("Score")
    plt.ylabel("Count")
    plt.legend()
    plt.savefig(os.path.join(output_dir, "score_distribution.png"))
    plt.close()

    # 2. Score Scatter Plot
    plt.figure()
    sns.scatterplot(
        data=df,
        x="pos_score",
        y="neg_score",
        hue="success",
        palette={True: "green", False: "red"},
    )
    plt.plot([0, 100], [0, 100], ls="--", c=".3")  # Diagonal line
    plt.axhline(y=70, color="r", linestyle="--", alpha=0.5, label="Neg Threshold (70)")
    plt.axvline(x=70, color="g", linestyle="--", alpha=0.5, label="Pos Threshold (70)")

    plt.title("Positive vs Negative Scores per Job")
    plt.xlabel("Positive Resume Score")
    plt.ylabel("Negative Resume Score")
    plt.legend()
    plt.savefig(os.path.join(output_dir, "score_scatter.png"))
    plt.close()

    # 3. Top Missing Skills
    if "missing_skills" in df.columns:
        all_skills = []
        for skills in df["missing_skills"]:
            if isinstance(skills, list):
                for s in skills:
                    if isinstance(s, dict) and "skill_name" in s:
                        all_skills.append(s["skill_name"])
                    elif isinstance(s, str):
                        all_skills.append(s)

        if all_skills:
            from collections import Counter

            skill_counts = Counter(all_skills).most_common(10)
            skills, counts = zip(*skill_counts)

            plt.figure(figsize=(12, 6))
            sns.barplot(x=list(counts), y=list(skills), palette="rocket")
            plt.title("Top 10 Missing Skills")
            plt.xlabel("Frequency")
            plt.tight_layout()
            plt.savefig(os.path.join(output_dir, "missing_skills.png"))
            plt.close()

    print(f"Saved recommendation charts to {output_dir}")


def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    results_dir = os.path.join(base_dir, "results")
    charts_dir = os.path.join(results_dir, "charts")

    ensure_dir(charts_dir)

    # Load Data
    retrieval_path = os.path.join(results_dir, "retrieval_evaluation.json")
    rec_path = os.path.join(results_dir, "evaluation_report.json")

    retrieval_data = load_json(retrieval_path)
    rec_data = load_json(rec_path)

    # Visualize
    visualize_retrieval(retrieval_data, charts_dir)
    visualize_recommendation(rec_data, charts_dir)

    print("\nDone! Charts saved in:", charts_dir)


if __name__ == "__main__":
    main()
