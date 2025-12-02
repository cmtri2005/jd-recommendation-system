from pydantic import BaseModel, Field
from typing import List 

class JD(BaseModel):
    """ALWAYS user this model to structure your response to the user."""
    job_summary: str = Field(description="A brief summary of the job description.")
    require_hard_skills: List[str] = Field(default=[], description="A list of required hard skills the job description mentioned. Otherwise, leave it empty.")
    optional_hard_skills: List[str] = Field(default=[], description="A list of optional hard skills the job description mentioned. Otherwise, leave it empty.")
    required_soft_skills: List[str] = Field(default=[], description="A list of required soft skills the job description mentioned. Otherwise, leave it empty.")
    optional_soft_skills: List[str] = Field(default=[], description="A list of optional soft skills the job description mentioned. Otherwise, leave it empty.")
    required_work_experiences: List[str] = Field(default=[], description="A list of required work experiences the job description mentioned. Otherwise, leave it empty.")
    optional_work_experiences: List[str] = Field(default=[], description="A list of optional work experiences the job description mentioned. Otherwise, leave it empty.")
    required_educations: List[str] = Field(default=[], description="A list of required educational backgrounds the job description mentioned. Otherwise, leave it empty.")
    optional_educations: List[str] = Field(default=[], description="A list of optional educational backgrounds the job description mentioned. Otherwise, leave it empty.")
    required_years_of_experience: int = Field(default=0, description="Total required years of experience the job description mentioned. Otherwise, leave it zero.")
    
    
    
    