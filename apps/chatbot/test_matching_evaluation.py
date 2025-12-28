"""
Test script for evaluating matching system with ground truth dataset
"""
import sys
import os
import json
from pathlib import Path
from typing import Optional

# Ensure we can import from core
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from core.agents.orchestrator import Orchestrator
from core.agents.state import State
from core.evaluation.matching_evaluator import MatchingEvaluator
from core.agents.evaluation_agent import EvaluationAgent
from core.factories.llm_factory import LLMFactory
from dotenv import load_dotenv

load_dotenv()


def create_sample_ground_truth(output_path: str):
    """
    Create a sample ground truth dataset file for testing
    
    Args:
        output_path: Path to save the ground truth file
    """
    # Example ground truth data
    # In practice, you would load this from your actual test dataset
    sample_data = [
        {
            "jd_path": "resume_jd/url.docx",
            "resume_path": "resume_jd/NGUYENMINHTRI_TEST.pdf",
            "label": "pass"  # or "score": 0.85
        },
        # Add more test pairs here
    ]
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(sample_data, f, indent=2, ensure_ascii=False)
    
    print(f"Sample ground truth created at: {output_path}")
    print(f"Please add your test JD-Resume pairs to this file")


def run_matching_evaluation(
    ground_truth_path: str,
    threshold: float = 0.7,
    output_results_path: Optional[str] = None
):
    """
    Run matching evaluation against ground truth dataset
    
    Args:
        ground_truth_path: Path to ground truth JSON/CSV file
        threshold: Score threshold for pass/fail (default: 0.7)
        output_results_path: Optional path to save evaluation results
    """
    print("=" * 80)
    print("MATCHING SYSTEM EVALUATION")
    print("=" * 80)
    
    # Initialize evaluator
    evaluator = MatchingEvaluator(threshold=threshold)
    
    # Load ground truth
    print(f"\nLoading ground truth from: {ground_truth_path}")
    try:
        ground_truth = evaluator.load_ground_truth(ground_truth_path)
        print(f"Loaded {len(ground_truth)} ground truth pairs")
    except Exception as e:
        print(f"Error loading ground truth: {e}")
        return
    
    # Initialize orchestrator for matching
    print("\nInitializing matching system...")
    try:
        orchestrator = Orchestrator()
        graph = orchestrator.orchestrate()
        evaluation_agent = EvaluationAgent(
            "evaluation_agent",
            orchestrator.llm,
            orchestrator.tools
        )
    except Exception as e:
        print(f"Error initializing matching system: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Run matching on each pair
    print(f"\nRunning matching on {len(ground_truth)} pairs...")
    predictions = []
    
    for i, gt_pair in enumerate(ground_truth, 1):
        jd_path = gt_pair['jd_path']
        resume_path = gt_pair['resume_path']
        
        # Convert relative paths to absolute if needed
        if not os.path.isabs(jd_path):
            jd_path = os.path.join(current_dir, jd_path)
        if not os.path.isabs(resume_path):
            resume_path = os.path.join(current_dir, resume_path)
        
        print(f"\n[{i}/{len(ground_truth)}] Processing:")
        print(f"  JD: {jd_path}")
        print(f"  Resume: {resume_path}")
        
        # Check if files exist
        if not os.path.exists(jd_path):
            print(f"  ⚠️  Warning: JD file not found, skipping...")
            continue
        if not os.path.exists(resume_path):
            print(f"  ⚠️  Warning: Resume file not found, skipping...")
            continue
        
        try:
            # Run matching using the graph
            initial_state = {
                "resume_path": resume_path,
                "jd_path": jd_path,
                "messages": []
            }
            
            result = graph.invoke(initial_state)
            
            # Extract resume and JD text from state
            resume_text = result.get("resume_text", "")
            jd_text = result.get("jd_text", "")
            
            if not resume_text or not jd_text:
                print(f"  ⚠️  Warning: Could not extract resume or JD text, skipping...")
                continue
            
            # Get matching score using evaluation agent
            eval_result = evaluation_agent.evaluate_with_score(
                resume=str(resume_text),
                jd=str(jd_text)
            )
            
            score = eval_result['score_normalized']  # Already normalized to 0-1
            
            predictions.append({
                'jd_path': gt_pair['jd_path'],  # Use original path for matching
                'resume_path': gt_pair['resume_path'],
                'score': score
            })
            
            print(f"  ✓ Score: {score:.4f} ({eval_result['score']:.2f}/100)")
            
        except Exception as e:
            error_msg = str(e)
            error_type = type(e).__name__
            
            # Check for specific error types
            if "RateLimitError" in error_type or "429" in error_msg or "rate_limit" in error_msg.lower():
                print(f"  ✗ Error: Rate limit exceeded!")
                print(f"    💡 Solution: Switch to Gemini by setting:")
                print(f"       LLM_PROVIDER=gemini")
                print(f"       GOOGLE_API_KEY=your_key")
                print(f"    Or wait for rate limit to reset (check error message for wait time)")
            elif "tool_use_failed" in error_msg or "Failed to call a function" in error_msg:
                print(f"  ✗ Error: LLM returned invalid format for JD extraction")
                print(f"    This usually happens when JD content is malformed or LLM fails to parse it correctly")
                print(f"    Error details: {error_msg[:200]}...")
            elif "years_of_experience" in error_msg:
                print(f"  ✗ Error: Schema validation failed (years_of_experience)")
            else:
                print(f"  ✗ Error processing pair: {error_msg[:300]}")
                # Only print full traceback for unexpected errors
                if "BadRequestError" not in error_type and "RateLimitError" not in error_type:
                    import traceback
                    traceback.print_exc()
            continue
    
    if len(predictions) == 0:
        print("\n⚠️  No predictions generated. Cannot evaluate.")
        return
    
    # Evaluate predictions against ground truth
    print(f"\n\nEvaluating {len(predictions)} predictions against ground truth...")
    try:
        results = evaluator.evaluate(ground_truth, predictions)
        
        # Print evaluation report
        evaluator.print_evaluation_report(results)
        
        # Save results if requested
        if output_results_path:
            evaluator.save_results(results, output_results_path)
        
        return results
        
    except Exception as e:
        print(f"Error during evaluation: {e}")
        import traceback
        traceback.print_exc()
        return None


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Evaluate matching system with ground truth')
    parser.add_argument(
        '--ground-truth',
        type=str,
        default='data/ground_truth.json',
        help='Path to ground truth JSON/CSV file'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.7,
        help='Score threshold for pass/fail classification (default: 0.7)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default=None,
        help='Path to save evaluation results (optional)'
    )
    parser.add_argument(
        '--create-sample',
        action='store_true',
        help='Create a sample ground truth file template'
    )
    
    args = parser.parse_args()
    
    if args.create_sample:
        create_sample_ground_truth(args.ground_truth)
        return
    
    # Run evaluation
    run_matching_evaluation(
        ground_truth_path=args.ground_truth,
        threshold=args.threshold,
        output_results_path=args.output
    )


if __name__ == "__main__":
    main()
