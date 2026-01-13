from pydantic import BaseModel, Field, field_validator
from typing import List, Literal, Optional


class ScoreBreakdown(BaseModel):
    """Detailed score breakdown for each evaluation category."""

    hard_skills_score: int = Field(
        ...,
        ge=0,
        le=30,
        description="Score for hard/technical skills match (0-30 points)",
    )
    soft_skills_score: int = Field(
        ..., ge=0, le=5, description="Score for soft skills match (0-5 points)"
    )
    work_experience_score: int = Field(
        ...,
        ge=0,
        le=30,
        description="Score for work experience relevance (0-30 points)",
    )
    years_of_experience_score: int = Field(
        ...,
        ge=0,
        le=15,
        description="Score for years of experience match (0-15 points)",
    )
    education_score: int = Field(
        ..., ge=0, le=10, description="Score for education match (0-10 points)"
    )
    extras_score: int = Field(
        ...,
        ge=0,
        le=10,
        description="Score for certifications, projects, awards (0-10 points)",
    )

    @field_validator(
        "hard_skills_score",
        "soft_skills_score",
        "work_experience_score",
        "years_of_experience_score",
        "education_score",
        "extras_score",
        mode="before",
    )
    @classmethod
    def clamp_scores(cls, v, info):
        """Clamp scores to valid ranges if LLM returns out-of-range values."""
        max_values = {
            "hard_skills_score": 30,
            "soft_skills_score": 5,
            "work_experience_score": 30,
            "years_of_experience_score": 15,
            "education_score": 10,
            "extras_score": 10,
        }
        field_name = info.field_name
        max_val = max_values.get(field_name, 100)
        return max(0, min(int(v), max_val))

    @property
    def total_score(self) -> int:
        """Calculate total score from all categories."""
        return (
            self.hard_skills_score
            + self.soft_skills_score
            + self.work_experience_score
            + self.years_of_experience_score
            + self.education_score
            + self.extras_score
        )


class SkillGap(BaseModel):
    """Information about a missing skill."""

    skill_name: str = Field(..., description="Name of the missing hard skill")
    importance: Literal["critical", "important", "nice-to-have"] = Field(
        ..., description="How critical this skill is for the job"
    )
    learning_resources: List[str] = Field(
        default_factory=list,
        description="List of URLs or references to learn this skill",
    )


class MatchStrength(BaseModel):
    """Areas where candidate is strong."""

    category: str = Field(
        ..., description="Category name (e.g., 'Hard Skills', 'Experience')"
    )
    details: str = Field(..., description="Brief explanation of why this is a strength")


class MatchWeakness(BaseModel):
    """Areas where candidate is lacking."""

    category: str = Field(
        ..., description="Category name (e.g., 'Hard Skills', 'Education')"
    )
    details: str = Field(..., description="Brief explanation of the gap")


class EvaluationResult(BaseModel):
    """Complete structured evaluation result for Resume vs JD matching."""

    total_score: int = Field(
        ..., ge=0, le=100, description="Total matching score out of 100"
    )

    score_breakdown: ScoreBreakdown = Field(
        ..., description="Detailed breakdown of scores by category"
    )

    strengths: List[MatchStrength] = Field(
        default_factory=list,
        description="Major strengths of the candidate for this role",
    )

    weaknesses: List[MatchWeakness] = Field(
        default_factory=list, description="Major gaps or missing areas"
    )

    missing_hard_skills: List[SkillGap] = Field(
        default_factory=list,
        description="Critical hard skills that the candidate is missing",
    )

    summary: str = Field(
        ...,
        min_length=50,
        max_length=500,
        description="3-4 line summary covering strengths and gaps",
    )

    recommendation: Literal["suitable", "not_suitable"] = Field(
        ..., description="Whether the JD is suitable for this resume"
    )

    recommendation_reason: str = Field(
        default="", description="Detailed reason for the recommendation"
    )

    @field_validator("total_score")
    def validate_total_matches_breakdown(cls, v, info):
        """Ensure total_score matches the sum of breakdown scores."""
        if "score_breakdown" in info.data:
            breakdown = info.data["score_breakdown"]
            calculated_total = breakdown.total_score
            if v != calculated_total:
                raise ValueError(
                    f"total_score ({v}) must match sum of breakdown ({calculated_total})"
                )
        return v

    @field_validator("recommendation")
    def validate_recommendation_threshold(cls, v, info):
        """Ensure recommendation aligns with score threshold."""
        if "total_score" in info.data:
            score = info.data["total_score"]
            if score >= 60 and v != "suitable":
                return "suitable"
            if score < 60 and v != "not_suitable":
                return "not_suitable"
        return v

    def format_display(self) -> str:
        """Format evaluation result for human-readable display."""
        icon = "✅" if self.recommendation == "suitable" else "❌"

        output = f"""
# Evaluation Result

## Overall Score: {self.total_score}/100 {icon}

### Score Breakdown
- Hard Skills: {self.score_breakdown.hard_skills_score}/30
- Soft Skills: {self.score_breakdown.soft_skills_score}/5
- Work Experience: {self.score_breakdown.work_experience_score}/30
- Years of Experience: {self.score_breakdown.years_of_experience_score}/15
- Education: {self.score_breakdown.education_score}/10
- Extras (Certs/Projects): {self.score_breakdown.extras_score}/10

### Summary
{self.summary}

### Strengths
"""
        for strength in self.strengths:
            output += f"- **{strength.category}**: {strength.details}\n"

        output += "\n### Weaknesses\n"
        for weakness in self.weaknesses:
            output += f"- **{weakness.category}**: {weakness.details}\n"

        if self.missing_hard_skills:
            output += "\n### Missing Critical Skills\n"
            for skill in self.missing_hard_skills:
                output += f"\n**{skill.skill_name}** ({skill.importance})\n"
                if skill.learning_resources:
                    output += "Resources:\n"
                    for resource in skill.learning_resources:
                        output += f"  - {resource}\n"

        output += f"\n### Recommendation\n{icon} {self.recommendation_reason}\n"

        return output
