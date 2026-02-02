"""
Unified Batch Runner for Evaluation Scripts

This script provides a command-line interface to run evaluation scripts
with comprehensive progress reporting and graceful interruption handling.
"""

import sys
import os
import subprocess
import argparse
import signal
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


class BatchRunner:
    """Orchestrator for running evaluation scripts."""

    def __init__(self):
        self.interrupted = False
        # Register signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle CTRL+C interruption."""
        print("\n\n⚠️  Interrupt received. Finishing current operation...")
        print("💡 Progress has been saved. You can resume by running the script again.")
        self.interrupted = True

    def run_evaluation(self, script_name: str, args: list) -> int:
        """
        Run an evaluation script with arguments.

        Args:
            script_name: Name of the evaluation script
            args: List of command-line arguments

        Returns:
            Exit code from the script
        """
        script_path = os.path.join(os.path.dirname(__file__), script_name)

        if not os.path.exists(script_path):
            print(f"❌ Error: Script not found: {script_path}")
            return 1

        print(f"\n{'='*70}")
        print(f"🚀 Starting: {script_name}")
        print(f"{'='*70}\n")

        # Build command
        cmd = [sys.executable, script_path] + args

        try:
            # Run the script
            result = subprocess.run(cmd, check=False)

            if result.returncode == 0:
                print(f"\n✅ {script_name} completed successfully")
            else:
                print(f"\n⚠️  {script_name} finished with exit code {result.returncode}")

            return result.returncode

        except KeyboardInterrupt:
            print(f"\n\n⚠️  {script_name} interrupted by user")
            return 130  # Standard exit code for CTRL+C
        except Exception as e:
            print(f"\n❌ Error running {script_name}: {e}")
            return 1


def main():
    parser = argparse.ArgumentParser(
        description="Unified Batch Runner for Evaluation Scripts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run recommendation evaluation with custom batch size
  python batch_runner.py --recommendation --batch-size 2 --max-items 5
  
  # Run retrieval evaluation
  python batch_runner.py --retrieval
  
  # Run both evaluations sequentially
  python batch_runner.py --both --max-items 10
  
  # Use custom configuration
  python batch_runner.py --recommendation --config custom_config.json
        """,
    )

    # Evaluation selection
    eval_group = parser.add_mutually_exclusive_group(required=False)
    eval_group.add_argument(
        "--recommendation", action="store_true", help="Run recommendation evaluation"
    )
    eval_group.add_argument(
        "--retrieval", action="store_true", help="Run retrieval evaluation"
    )
    eval_group.add_argument(
        "--both", action="store_true", help="Run both evaluations sequentially"
    )

    # Configuration options
    parser.add_argument(
        "--config", type=str, help="Path to batch configuration JSON file"
    )
    parser.add_argument("--batch-size", type=int, help="Override batch size")
    parser.add_argument(
        "--batch-delay", type=float, help="Override batch delay in seconds"
    )
    parser.add_argument(
        "--item-delay", type=float, help="Override item delay in seconds"
    )
    parser.add_argument(
        "--max-items", type=int, help="Maximum number of items to process (for testing)"
    )
    parser.add_argument(
        "--visualize",
        action="store_true",
        default=True,
        help="Run visualization scripts after evaluation (default: True)",
    )

    args = parser.parse_args()

    # Default to recommendation if nothing specified
    if not (args.recommendation or args.retrieval or args.both):
        args.recommendation = True

    # Build argument list to pass to evaluation scripts
    script_args = []
    if args.config:
        script_args.extend(["--config", args.config])
    if args.batch_size is not None:
        script_args.extend(["--batch-size", str(args.batch_size)])
    if args.batch_delay is not None:
        script_args.extend(["--batch-delay", str(args.batch_delay)])
    if args.item_delay is not None:
        script_args.extend(["--item-delay", str(args.item_delay)])
    if args.max_items is not None:
        script_args.extend(["--max-items", str(args.max_items)])

    runner = BatchRunner()

    print("\n" + "=" * 70)
    print("🎯 BATCH EVALUATION RUNNER")
    print("=" * 70)
    print(f"📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    exit_codes = []

    try:
        # Run recommendation evaluation
        if args.recommendation or args.both:
            exit_code = runner.run_evaluation("eval_recommendation.py", script_args)
            exit_codes.append(("Recommendation", exit_code))

            if runner.interrupted:
                return exit_code

        # Run retrieval evaluation
        if args.retrieval or args.both:
            exit_code = runner.run_evaluation("eval_retrieval.py", script_args)
            exit_codes.append(("Retrieval", exit_code))

            if runner.interrupted:
                return exit_code

        # Summary
        print("\n" + "=" * 70)
        print("📊 BATCH RUNNER SUMMARY")
        print("=" * 70)
        print(f"📅 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("\nResults:")

        all_success = True
        for name, code in exit_codes:
            status = "✅ Success" if code == 0 else f"⚠️  Exit code {code}"
            print(f"  {name}: {status}")
            if code != 0:
                all_success = False

        print("=" * 70)

        if all_success:
            print("\n🎉 All evaluations completed successfully!")

            # Run visualization if requested
            if args.visualize:
                print("\n" + "=" * 70)
                print("🎨 RUNNING VISUALIZATION")
                print("=" * 70)

                viz_scripts = ["visualize_results_static.py", "visualize_metrics.py"]
                viz_success = True

                for script in viz_scripts:
                    if os.path.exists(os.path.join(os.path.dirname(__file__), script)):
                        code = runner.run_evaluation(script, [])
                        if code != 0:
                            viz_success = False

                if viz_success:
                    print("\n✨ Visualization completed successfully!")

            return 0
        else:
            print("\n⚠️  Some evaluations had issues. Check logs for details.")
            return 1

    except Exception as e:
        print(f"\n❌ Batch runner error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
