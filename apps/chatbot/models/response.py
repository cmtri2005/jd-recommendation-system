"""Response models for API endpoints."""

from pydantic import BaseModel
from typing import List, Literal


class LearningResourceResponse(BaseModel):
    """Learning resource from KB."""

    title: str
    organization: str
    url: str
    rating: str
    difficulty: str
    type: str
    verified: bool = True


class SkillGapResponse(BaseModel):
    """Missing skill with learning resources."""

    skill_name: str
    importance: Literal["critical", "important", "nice-to-have"]
    learning_resources: List[str]


class ScoreBreakdownResponse(BaseModel):
    """Score breakdown."""

    hard_skills_score: int
    soft_skills_score: int
    work_experience_score: int
    years_of_experience_score: int
    education_score: int
    extras_score: int


class MatchItemResponse(BaseModel):
    """Strength or weakness item."""

    category: str
    details: str


class EvaluationResponse(BaseModel):
    """Evaluation result response."""

    total_score: int
    score_breakdown: ScoreBreakdownResponse
    strengths: List[MatchItemResponse]
    weaknesses: List[MatchItemResponse]
    missing_hard_skills: List[SkillGapResponse]
    summary: str
    recommendation: Literal["suitable", "not_suitable"]
    recommendation_reason: str
    retrieved_jobs: List[str] = []
