from pydantic import BaseModel, Field
from typing import List
from schemas.experience import Experience


class Resume(BaseModel):
    """ALWAYS use this model to structure your response to the user."""

    profile_summary: str = Field(
        description="A brief summary of the applicant's profile."
    )
    hard_skills: List[str] = Field(
        default=[], description="A list of hard skills possessed by the applicant."
    )
    soft_skills: List[str] = Field(
        default=[], description="A list of the applicant's soft skills if available."
    )
    work_experiences: List[Experience] = Field(
        default=[],
        description="A list of work experiences held by the applicant if available.",
    )
    educations: List[str] = Field(
        default=[],
        description="The list of educational backgrounds of the applicant if available.",
    )
    years_of_experience: int = Field(
        default=0,
        description="Total years of experience in the field if work experience is available. Otherwise, leave it zero.",
    )
    certifications: List[str] = Field(
        default=[],
        description="A list of certifications held by the applicant if available.",
    )
    projects: List[str] = Field(
        default=[],
        description="A list of projects. If work experience is not available or less than 1 year, this field is required. Otherwise, leave it empty.",
    )
