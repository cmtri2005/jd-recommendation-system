
import json
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_DIR = os.path.join(BASE_DIR, 'results')
PLOTS_DIR = os.path.join(RESULTS_DIR, 'plots')
EVALUATION_REPORT_PATH = os.path.join(RESULTS_DIR, 'evaluation_report.json')
RETRIEVAL_EVALUATION_PATH = os.path.join(RESULTS_DIR, 'retrieval_evaluation.json')

# Create plots directory if it doesn't exist
os.makedirs(PLOTS_DIR, exist_ok=True)

def load_json(path):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def visualize_evaluation_report(data):
    if not data:
        return

    df = pd.DataFrame(data)
    
    # 1. Distribution of Positive Scores
    plt.figure(figsize=(10, 6))
    sns.histplot(df['pos_score'], bins=20, kde=True, color='green')
    plt.title('Distribution of Positive Scores')
    plt.xlabel('Positive Score')
    plt.ylabel('Count')
    plt.savefig(os.path.join(PLOTS_DIR, 'pos_score_distribution.png'))
    plt.close()

    # 2. Distribution of Negative Scores
    plt.figure(figsize=(10, 6))
    sns.histplot(df['neg_score'], bins=20, kde=True, color='red')
    plt.title('Distribution of Negative Scores')
    plt.xlabel('Negative Score')
    plt.ylabel('Count')
    plt.savefig(os.path.join(PLOTS_DIR, 'neg_score_distribution.png'))
    plt.close()

    # 3. Success vs Failure
    plt.figure(figsize=(6, 6))
    success_counts = df['success'].value_counts()
    plt.pie(success_counts, labels=success_counts.index, autopct='%1.1f%%', colors=['skyblue', 'lightcoral'])
    plt.title('Success vs Failure Rate')
    plt.savefig(os.path.join(PLOTS_DIR, 'success_rate.png'))
    plt.close()

    # 4. Scatter Plot: Positive vs Negative Scores
    plt.figure(figsize=(10, 6))
    sns.scatterplot(data=df, x='pos_score', y='neg_score', hue='success', palette={True: 'green', False: 'red'})
    plt.title('Positive vs Negative Scores')
    plt.xlabel('Positive Score')
    plt.ylabel('Negative Score')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.savefig(os.path.join(PLOTS_DIR, 'pos_vs_neg_scatter.png'))
    plt.close()
    
    print(f"Evaluation report plots saved to {PLOTS_DIR}")

def visualize_retrieval_evaluation(data):
    if not data:
        return

    metrics = data.get('metrics', {})
    
    # Text-based visualization for metrics
    plt.figure(figsize=(8, 4))
    plt.axis('off')
    
    text_str = "Retrieval Evaluation Metrics\n\n"
    for key, value in metrics.items():
        text_str += f"{key}: {value}\n"
        
    plt.text(0.5, 0.5, text_str, ha='center', va='center', fontsize=14, family='monospace')
    plt.title("Retrieval Metrics Summary", fontsize=16)
    plt.savefig(os.path.join(PLOTS_DIR, 'retrieval_metrics.png'))
    plt.close()
    
    print(f"Retrieval evaluation plots saved to {PLOTS_DIR}")

def main():
    print("Loading data...")
    eval_report_data = load_json(EVALUATION_REPORT_PATH)
    retrieval_data = load_json(RETRIEVAL_EVALUATION_PATH)

    print("Generating plots...")
    visualize_evaluation_report(eval_report_data)
    visualize_retrieval_evaluation(retrieval_data)
    print("Done.")

if __name__ == "__main__":
    main()
