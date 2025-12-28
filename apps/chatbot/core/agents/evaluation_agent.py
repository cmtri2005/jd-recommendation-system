from typing import Annotated, Literal, TypedDict, Sequence, Callable
from langgraph.graph import END, START, StateGraph, MessagesState
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from core.agents.base_agent import BaseAgent
from dotenv import load_dotenv


load_dotenv()


class EvaluationAgent(BaseAgent):
    """Agent for evaluation matching score between resume and jd"""

    def __init__(self, name: str, llm: BaseChatModel, tools: list[Callable]):
        super().__init__(name, llm, tools)
        self.name = "evaluation_agent"
        self.prompt = self.evaluation_agent_chat_prompt_template()

    def evaluation_agent_chat_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate(
            [
                (
                    "system",
                    """
                    Your task is to evaluate how well a candidate's resume matches a given job description and 
                    mark a score from 0 to 100 based on the criteria below.

                    Scoring criteria:
                    - **Hard Skills Match: 30 points**
                    - **Soft Skills Match: 5 points**
                    - **Work Experiences Match: 30 points**
                        - Do NOT award experience points for roles **unrelated** to the job description.
                        - For intern, fresher:
                            - Evaluate based on relavant internships, academic projects, persone projects or porfolio work that aligns with the job.
                        - For experiences candidates:
                            - Evaluate based on **quality, relevance, and impact** of work (e.g., problem-solving, outcomes, tools used).
                    - **Years Of Experiences Match: 15 points**
                    - **Education of Score: 10 points**
                    - **Extras (Certifications, Side Project, Award): 10 points**
                   Instructions:
                    - Extract and compare the candidate’s **skills**, **experience**, **education**, and **additional qualifications** to the job description.
                    - Apply the scoring rules strictly, especially for experience and education.
                    - Do not award points for irrelevant experience.

                    After evaluation, return:
                    1. **Total score (out of 100)**
                    2. **Score breakdown by category** (e.g., Skills: 24/30, Experience: 32/50)
                    3. **A short summary** (3–4 lines) covering major strengths and missing areas.
                    4. **Lists of missing hard skill**: A list of hard skills that resume's user missing to pass JD.
                    5. **References**: You apply some references that can be a document, blog resource, tutorial, v.v for user to improve their hard skills missing.
                    5. **A final recommendation**, based on these rules:
                        - If the candidate scores **above 70** and meets the key job requirements:
                            - Say: **✅ JD was suitable for your resume.**
                        - If the candidate scores **below 70**:
                            - Say: **❌ Your resume deos not match this JD.**
                            - Follow with a reason based on the biggest gaps (skills, experience, or education).
                """,
                ),
                (
                    "user",
                    "Please provide matching score between {resume_text} and {jd_text}",
                ),
            ]
        )

    def evaluate(self, resume: str, jd: str):
        chain = self.prompt | self.llm
        result = chain.invoke({"resume_text": resume, "jd_text": jd})
        return result.content
