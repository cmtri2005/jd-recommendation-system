import os
import operator
from typing import List, TypedDict, Annotated, Optional
from schema.jd import JD
from schema.resume import Resume


class State(TypedDict):
    """State for LangGraph orchestration. Must use TypedDict for LangGraph compatibility."""

    resume_path: str
    jd_path: str
    resume_text: Optional[Resume]
    jd_text: Optional[JD]
    messages: Annotated[List[str], operator.add]
    retrieved_jobs: List[str]


def validate_state_paths(state: State) -> None:
    """Validate state paths before processing.

    Args:
        state: The state dict to validate

    Raises:
        ValueError: If paths are invalid
        FileNotFoundError: If files don't exist
    """
    resume_path = state.get("resume_path")
    jd_path = state.get("jd_path")

    if not resume_path:
        raise ValueError("resume_path is missing or empty in state")
    if not jd_path:
        raise ValueError("jd_path is missing or empty in state")

    if not os.path.exists(resume_path):
        raise FileNotFoundError(f"Resume file not found: {resume_path}")
    if not os.path.exists(jd_path):
        raise FileNotFoundError(f"JD file not found: {jd_path}")
