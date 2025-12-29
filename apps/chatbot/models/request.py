"""Request models for API endpoints."""

from pydantic import BaseModel, Field


class EvaluationRequest(BaseModel):
    """Request model for evaluation endpoint."""

    resume_text: str = Field(..., description="Resume content as text")
    jd_text: str = Field(..., description="Job description as text")
