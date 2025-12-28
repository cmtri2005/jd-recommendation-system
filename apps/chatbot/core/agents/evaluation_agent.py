from typing import Annotated, Literal, TypedDict, Sequence, Callable, Dict, Optional
from langgraph.graph import END, START, StateGraph, MessagesState
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from core.agents.base_agent import BaseAgent
from dotenv import load_dotenv
import re


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

                    After evaluation, return in the following format:
                    1. **Total score (out of 100)** - MUST be in format: "Total score: XX/100" or "Score: XX"
                    2. **Score breakdown by category** (e.g., Skills: 24/30, Experience: 32/50)
                    3. **A short summary** (3–4 lines) covering major strengths and missing areas.
                    4. **A final recommendation**, based on these rules:
                        - If the candidate scores **above 75** and meets the key job requirements:
                            - Say: **✅ I recommend this candidate for the job.**
                        - If the candidate scores **between 50 and 75**, with partial matches in skills or experience:
                            - Say: **❌ I do not recommend this candidate for this specific job.**
                            - Follow with: **However, I recommend this candidate for an internship or entry-level position, as they show foundational potential.**
                        - If the candidate scores **below 50**:
                            - Say: **❌ I do not recommend this candidate for the job.**
                            - Follow with a reason based on the biggest gaps (skills, experience, or education).
                """,
                ),
                (
                    "user",
                    "Please provide matching score between {resume_text} and {jd_text}",
                ),
            ]
        )

    def evaluate(self, resume: str, jd: str) -> str:
        """Evaluate matching score and return text response"""
        chain = self.prompt | self.llm
        result = chain.invoke({"resume_text": resume, "jd_text": jd})
        return result.content

    def evaluate_with_score(self, resume: str, jd: str) -> Dict[str, any]:
        """Evaluate matching score and return structured result with numeric score"""
        text_result = self.evaluate(resume, jd)
        score = self._extract_score(text_result)
        return {
            "score": score,
            "score_normalized": score / 100.0,  # Normalize to 0-1 range
            "text": text_result
        }

    def _extract_score(self, text: str) -> float:
        """Extract numeric score from LLM response text"""
        # Try multiple patterns to extract score
        patterns = [
            r"Total score:\s*(\d+(?:\.\d+)?)\s*/?\s*100",
            r"Score:\s*(\d+(?:\.\d+)?)\s*/?\s*100",
            r"(\d+(?:\.\d+)?)\s*/?\s*100",
            r"score of\s*(\d+(?:\.\d+)?)",
            r"(\d+(?:\.\d+)?)\s*out of\s*100",
            r"(\d+(?:\.\d+)?)\s*points",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                score = float(match.group(1))
                # Ensure score is in valid range
                if 0 <= score <= 100:
                    return score
        
        # If no pattern matches, try to find any number between 0-100
        numbers = re.findall(r'\b(\d+(?:\.\d+)?)\b', text)
        for num_str in numbers:
            num = float(num_str)
            if 0 <= num <= 100:
                return num
        
        # Default: return 0 if no score found
        self.logger.warning(f"Could not extract score from text: {text[:200]}...")
        return 0.0