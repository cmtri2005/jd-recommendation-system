from pydantic import BaseModel, Field
from typing import List


class ResumeResponsibility(BaseModel):
    """Model representing the responsibility per task."""
    task: str = Field(description="The specific task.")
    techstack: str = Field(description="Techstack that used in the task.")
    achievement: str = Field(description="The achievement after finish the task.")
