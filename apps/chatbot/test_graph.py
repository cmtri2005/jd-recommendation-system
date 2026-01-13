import sys
import os

# Ensure we can import from core
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

from core.agents.orchestrator import Orchestrator
from core.agents.state import State


def main():
    print("Initializing Orchestrator...")
    orchestrator = Orchestrator()
    graph = orchestrator.orchestrate()

    # Define paths
    resume_path = os.path.join(current_dir, "assets/Cao_Minh_Tri_Resume.pdf")
    jd_path = os.path.join(current_dir, "assets/url.docx")

    print(f"Resume Path: {resume_path}")
    print(f"JD Path: {jd_path}")

    if not os.path.exists(resume_path):
        print(f"Error: Resume file not found at {resume_path}")
        return
    if not os.path.exists(jd_path):
        print(f"Error: JD file not found at {jd_path}")
        return

    # Initial State
    initial_state = {"resume_path": resume_path, "jd_path": jd_path, "messages": []}

    print("\nInvoking Graph...")
    try:
        result = graph.invoke(initial_state)
        print("\nGraph Execution Completed Successfully!")
        print("-" * 50)
        print("Final State Keys:", result.keys())
        print("-" * 50)

        messages = result.get("messages", [])
        if messages:
            print("\n" + "=" * 50)
            print("EVALUATION RESULT:")
            print("=" * 50)
            # Last message is from evaluation
            eval_result = messages[-1]
            print(eval_result)

            # ✅ NEW: Verify Learning Resources KB Integration
            print("\n" + "=" * 50)
            print("LEARNING RESOURCES VERIFICATION:")
            print("=" * 50)

            # Check if evaluation result is EvaluationResult object (direct access)
            if hasattr(eval_result, "missing_hard_skills"):
                # Direct object access (EvaluationResult)
                missing_skills = eval_result.missing_hard_skills

                if missing_skills:
                    print(
                        f"\n✅ Found {len(missing_skills)} missing skills with learning resources:"
                    )

                    verified_count = 0
                    hallucinated_count = 0

                    for i, skill_gap in enumerate(missing_skills, 1):
                        skill_name = skill_gap.skill_name
                        resources = skill_gap.learning_resources
                        importance = skill_gap.importance

                        print(f"\n  {i}. Skill: {skill_name}")
                        print(f"     Importance: {importance}")
                        print(f"     Resources ({len(resources)}):")

                        for j, resource in enumerate(resources, 1):
                            print(f"       {j}. {resource}")

                            # Verify it's from verified dataset (contains coursera.org)
                            if "coursera.org" in resource.lower():
                                verified_count += 1
                                print(f"          ✅ VERIFIED (from KB)")
                            elif resource.startswith("http"):
                                hallucinated_count += 1
                                print(
                                    f"          ⚠️  WARNING: Non-KB URL (LLM hallucination)"
                                )
                            else:
                                print(f"          ℹ️  Non-URL resource")

                    # Summary
                    print("\n" + "-" * 50)
                    print("VERIFICATION SUMMARY:")
                    print(f"  ✅ Verified KB resources: {verified_count}")
                    print(f"  ⚠️  LLM hallucinations: {hallucinated_count}")

                    if hallucinated_count == 0:
                        print("\n  🎉 SUCCESS! All resources are from verified KB!")
                    else:
                        print(
                            f"\n  ❌ FAILURE! Found {hallucinated_count} hallucinated resources"
                        )
                        print("  📝 KB enrichment may not be working properly")
                    print("-" * 50)
                else:
                    print(
                        "\n✅ No missing skills found (candidate is fully qualified!)"
                    )

            elif hasattr(eval_result, "content"):
                # Fallback: try JSON parsing
                try:
                    import json

                    eval_data = json.loads(eval_result.content)
                    missing_skills = eval_data.get("missing_hard_skills", [])
                    if missing_skills:
                        print(f"Found {len(missing_skills)} skills (JSON format)")
                except Exception as e:
                    print(f"⚠️  Could not parse JSON: {e}")
            else:
                print("⚠️  Evaluation result format not recognized")
        else:
            print("No messages in result.")

        # Print recommended jobs from vector database
        retrieved_jobs = result.get("retrieved_jobs", [])
        if retrieved_jobs:
            print("\n" + "=" * 50)
            print("RECOMMENDED JOBS FROM VECTOR DATABASE:")
            print("=" * 50)
            for i, job in enumerate(retrieved_jobs, 1):
                print(f"\n--- Job {i} ---")
                print(job)
        else:
            print("\nNo recommended jobs found.")

    except Exception as e:
        print(f"\nGraph Execution Failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
