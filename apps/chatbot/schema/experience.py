from pydantic import BaseModel, Field
from typing import List
from schema.responsibility import Responsibility

class Experience(BaseModel):
    """Model representing the work experience entry in a resume."""    
    job_title: str = Field(description="Job title of the applicant.")
    company: str = Field(description="The company where the applicant worked.")
    employment_period: str = Field(description="The applicant's tenure at the company.")
    responsibilities: List[str] = Field(default=[], description="A list of responsibilities held in the position.")
    
    