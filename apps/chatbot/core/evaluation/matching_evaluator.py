"""
Matching Evaluator for comparing matching system results with ground truth dataset
"""
from typing import List, Dict, Tuple, Optional
import os
import json
from pathlib import Path
import numpy as np
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)
import pandas as pd


class MatchingEvaluator:
    """Evaluator for matching system accuracy and reliability"""
    
    def __init__(self, threshold: float = 0.7):
        """
        Initialize evaluator
        
        Args:
            threshold: Score threshold for pass/fail classification (default: 0.7)
        """
        self.threshold = threshold
    
    def load_ground_truth(self, ground_truth_path: str) -> List[Dict]:
        """
        Load ground truth dataset from file
        
        Expected format (JSON or CSV):
        - JSON: List of dicts with keys: jd_path, resume_path, label (pass/fail) or score
        - CSV: Columns: jd_path, resume_path, label or score
        
        Args:
            ground_truth_path: Path to ground truth file
            
        Returns:
            List of ground truth records
        """
        path = Path(ground_truth_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Ground truth file not found: {ground_truth_path}")
        
        if path.suffix == '.json':
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        elif path.suffix == '.csv':
            df = pd.read_csv(path)
            data = df.to_dict('records')
        else:
            raise ValueError(f"Unsupported file format: {path.suffix}. Use .json or .csv")
        
        # Normalize data format
        normalized_data = []
        for record in data:
            # Convert label to score if needed
            if 'label' in record:
                score = 1.0 if record['label'].lower() in ['pass', 'true', '1', 'yes'] else 0.0
            elif 'score' in record:
                score = float(record['score'])
            else:
                raise ValueError("Ground truth must have 'label' or 'score' field")
            
            normalized_data.append({
                'jd_path': record['jd_path'],
                'resume_path': record['resume_path'],
                'ground_truth_score': score,
                'ground_truth_label': 'pass' if score >= self.threshold else 'fail'
            })
        
        return normalized_data
    
    def predict_label(self, score: float) -> str:
        """Convert score to pass/fail label"""
        return 'pass' if score >= self.threshold else 'fail'
    
    def evaluate(
        self,
        ground_truth: List[Dict],
        predictions: List[Dict]
    ) -> Dict:
        """
        Evaluate matching system against ground truth
        
        Args:
            ground_truth: List of ground truth records
            predictions: List of prediction records with keys: jd_path, resume_path, score
            
        Returns:
            Dictionary with evaluation metrics
        """
        # Create lookup dict for predictions
        pred_dict = {
            (pred['jd_path'], pred['resume_path']): pred['score']
            for pred in predictions
        }
        
        # Match ground truth with predictions
        y_true = []
        y_pred = []
        y_true_scores = []
        y_pred_scores = []
        matched_pairs = []
        
        for gt in ground_truth:
            key = (gt['jd_path'], gt['resume_path'])
            if key in pred_dict:
                pred_score = pred_dict[key]
                gt_score = gt['ground_truth_score']
                
                y_true.append(gt['ground_truth_label'])
                y_pred.append(self.predict_label(pred_score))
                y_true_scores.append(gt_score)
                y_pred_scores.append(pred_score)
                
                matched_pairs.append({
                    'jd_path': gt['jd_path'],
                    'resume_path': gt['resume_path'],
                    'ground_truth_score': gt_score,
                    'predicted_score': pred_score,
                    'ground_truth_label': gt['ground_truth_label'],
                    'predicted_label': self.predict_label(pred_score),
                    'match': gt['ground_truth_label'] == self.predict_label(pred_score)
                })
        
        if len(y_true) == 0:
            raise ValueError("No matching pairs found between ground truth and predictions")
        
        # Calculate classification metrics
        accuracy = accuracy_score(y_true, y_pred)
        precision = precision_score(y_true, y_pred, pos_label='pass', zero_division=0)
        recall = recall_score(y_true, y_pred, pos_label='pass', zero_division=0)
        f1 = f1_score(y_true, y_pred, pos_label='pass', zero_division=0)
        cm = confusion_matrix(y_true, y_pred, labels=['fail', 'pass'])
        
        # Calculate score correlation
        score_correlation = np.corrcoef(y_true_scores, y_pred_scores)[0, 1] if len(y_true_scores) > 1 else 0.0
        mae = np.mean(np.abs(np.array(y_true_scores) - np.array(y_pred_scores)))
        mse = np.mean((np.array(y_true_scores) - np.array(y_pred_scores)) ** 2)
        rmse = np.sqrt(mse)
        
        # Classification report
        class_report = classification_report(
            y_true, y_pred, 
            labels=['fail', 'pass'],
            target_names=['fail', 'pass'],
            output_dict=True,
            zero_division=0
        )
        
        return {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1_score': f1,
            'confusion_matrix': cm.tolist(),
            'confusion_matrix_labels': ['fail', 'pass'],
            'score_correlation': score_correlation,
            'mae': mae,
            'mse': mse,
            'rmse': rmse,
            'classification_report': class_report,
            'num_samples': len(matched_pairs),
            'matched_pairs': matched_pairs,
            'threshold': self.threshold
        }
    
    def print_evaluation_report(self, results: Dict):
        """Print formatted evaluation report"""
        print("=" * 80)
        print("MATCHING SYSTEM EVALUATION REPORT")
        print("=" * 80)
        print(f"\nThreshold: {results['threshold']}")
        print(f"Number of samples: {results['num_samples']}")
        print("\n" + "-" * 80)
        print("CLASSIFICATION METRICS")
        print("-" * 80)
        print(f"Accuracy:  {results['accuracy']:.4f} ({results['accuracy']*100:.2f}%)")
        print(f"Precision: {results['precision']:.4f} ({results['precision']*100:.2f}%)")
        print(f"Recall:    {results['recall']:.4f} ({results['recall']*100:.2f}%)")
        print(f"F1 Score:  {results['f1_score']:.4f} ({results['f1_score']*100:.2f}%)")
        
        print("\n" + "-" * 80)
        print("SCORE METRICS")
        print("-" * 80)
        print(f"Score Correlation: {results['score_correlation']:.4f}")
        print(f"MAE (Mean Absolute Error): {results['mae']:.4f}")
        print(f"MSE (Mean Squared Error):  {results['mse']:.4f}")
        print(f"RMSE (Root Mean Squared Error): {results['rmse']:.4f}")
        
        print("\n" + "-" * 80)
        print("CONFUSION MATRIX")
        print("-" * 80)
        cm = results['confusion_matrix']
        labels = results['confusion_matrix_labels']
        print(f"\n{'':<10} {'Predicted Fail':<15} {'Predicted Pass':<15}")
        for i, label in enumerate(labels):
            print(f"{'Actual ' + label.capitalize():<10} {cm[i][0]:<15} {cm[i][1]:<15}")
        
        print("\n" + "-" * 80)
        print("DETAILED CLASSIFICATION REPORT")
        print("-" * 80)
        report = results['classification_report']
        for label in ['fail', 'pass']:
            if label in report:
                print(f"\n{label.upper()}:")
                print(f"  Precision: {report[label]['precision']:.4f}")
                print(f"  Recall:    {report[label]['recall']:.4f}")
                print(f"  F1-score:  {report[label]['f1-score']:.4f}")
                print(f"  Support:   {report[label]['support']}")
        
        print("\n" + "=" * 80)
    
    def save_results(self, results: Dict, output_path: str):
        """Save evaluation results to file"""
        output_path = Path(output_path)
        
        # Create parent directory if it doesn't exist
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Prepare data for saving (remove matched_pairs if too large)
        save_data = results.copy()
        if len(save_data.get('matched_pairs', [])) > 1000:
            save_data['matched_pairs'] = save_data['matched_pairs'][:1000]  # Keep only first 1000
        
        if output_path.suffix == '.json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
        elif output_path.suffix == '.csv':
            # Save matched pairs as CSV
            df = pd.DataFrame(save_data['matched_pairs'])
            df.to_csv(output_path, index=False)
        else:
            raise ValueError(f"Unsupported output format: {output_path.suffix}")
        
        print(f"\nResults saved to: {output_path}")
