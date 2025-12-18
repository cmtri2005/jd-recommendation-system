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
    initial_state = {
        "resume_path": resume_path,
        "jd_path": jd_path,
        "messages": []
    }

    print("\nInvoking Graph...")
    try:
        result = graph.invoke(initial_state)
        print("\nGraph Execution Completed Successfully!")
        print("-" * 50)
        print("Final State Keys:", result.keys())
        print("-" * 50)
        
        messages = result.get("messages", [])
        if messages:
            print("Evaluation Result:")
            # Last message is from evaluation
            print(messages[-1])
        else:
            print("No messages in result.")
            
    except Exception as e:
        print(f"\nGraph Execution Failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
