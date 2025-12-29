from pydantic import BaseModel, Field
from typing import Optional, Dict, Any


class Retrieval(BaseModel):
    query: str = Field(
        default="",
        description="User input",
    )
    tok_k: int = Field(default=3, description="Number of results to return")
    with_score: bool = Field(
        default=False, description="Whether to return the score of the results"
    )
    metadata_filter: Optional[Dict[str, Any]] = Field(
        default=None,
        description=(
            "Optional metadata filter for search. If unused, omit this field; do not send null."
        ),
    )
