import operator
from typing import List, TypedDict, Annotated
from schema.jd import JD
from schema.resume import Resume


class State(TypedDict):
    resume_path: str
    jd_path: str
    resume_text: Resume
    jd_text: JD
    messages: Annotated[List, operator.add]
    retrieved_jobs: List
