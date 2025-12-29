from typing import Annotated, Literal, TypedDict, Sequence, Callable
from langgraph.graph import END, START, StateGraph, MessagesState
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from core.agents.base_agent import BaseAgent
from schemas.evaluation import EvaluationResult
from services.learning_resources_service import get_learning_resources_service
from dotenv import load_dotenv


load_dotenv()


class EvaluationAgent(BaseAgent):
    """Agent for evaluation matching score between resume and jd"""

    def __init__(self, name: str, llm: BaseChatModel, tools: list[Callable]):
        super().__init__(name, llm, tools)
        self.name = "evaluation_agent"
        self.prompt = self.evaluation_agent_chat_prompt_template()
        # Initialize learning resources service
        self.learning_resources = get_learning_resources_service()

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
                    - Extract and compare the candidate's **skills**, **experience**, **education**, and **additional qualifications** to the job description.
                    - Apply the scoring rules strictly, especially for experience and education.
                    - Do not award points for irrelevant experience.

                    You must return a structured JSON response with:
                    1. **total_score**: Total score (0-100)
                    2. **score_breakdown**: Object with individual scores:
                       - hard_skills_score (0-30)
                       - soft_skills_score (0-5)
                       - work_experience_score (0-30)
                       - years_of_experience_score (0-15)
                       - education_score (0-10)
                       - extras_score (0-10)
                    3. **strengths**: Array of {{category, details}} for major strengths
                    4. **weaknesses**: Array of {{category, details}} for gaps
                    5. **missing_hard_skills**: Array of {{skill_name, importance, learning_resources[]}} 
                    6. **summary**: 3-4 line summary covering strengths and missing areas
                    7. **recommendation**: "suitable" if score >= 60, else "not_suitable"
                    8. **recommendation_reason**: REQUIRED - Detailed explanation of why suitable/not suitable
                    
                    Example for recommendation_reason:
                    - If suitable: "The candidate has strong technical skills matching 90% of requirements..."
                    - If not suitable: "The candidate lacks critical AWS and Kubernetes experience..."
                    
                    IMPORTANT: Ensure total_score equals the sum of all breakdown scores!
                """,
                ),
                (
                    "user",
                    "Please provide matching score between {resume_text} and {jd_text}",
                ),
            ]
        )

    def evaluate(self, resume: str, jd: str) -> EvaluationResult:
        """Evaluate resume against JD and return structured result.

        Args:
            resume: Resume text or Resume object
            jd: JD text or JD object

        Returns:
            EvaluationResult with structured scores and recommendations
        """
        # Convert objects to strings if needed
        resume_text = (
            resume.model_dump_json()
            if hasattr(resume, "model_dump_json")
            else str(resume)
        )
        jd_text = jd.model_dump_json() if hasattr(jd, "model_dump_json") else str(jd)

        # Use structured output
        chain = self.prompt | self.llm.with_structured_output(EvaluationResult)
        result = chain.invoke({"resume_text": resume_text, "jd_text": jd_text})

        # Enrich missing skills with verified learning resources
        result = self._enrich_skill_gaps_with_verified_resources(result)

        self.logger.info(f"Evaluation complete: Score={result.total_score}/100")
        return result

    def _enrich_skill_gaps_with_verified_resources(
        self, result: EvaluationResult
    ) -> EvaluationResult:
        """Enrich skill gaps with verified learning resources from KB.

        Replaces LLM-generated learning resources with verified ones from the course dataset.
        Falls back to LLM suggestions if KB doesn't have resources for a skill.

        Args:
            result: Original evaluation result from LLM

        Returns:
            Evaluation result with enriched, verified learning resources
        """
        if not result.missing_hard_skills:
            self.logger.info("🔍 No missing skills to enrich")
            return result

        self.logger.info(
            f"🔍 Enriching {len(result.missing_hard_skills)} missing skills with KB resources..."
        )

        for skill_gap in result.missing_hard_skills:
            verified_resources = self.learning_resources.get_resources_for_skill(
                skill_gap.skill_name,
                max_results=3,
                min_rating=4.0,
            )

            if verified_resources:
                # Replace with verified resources
                skill_gap.learning_resources = [
                    f"{r['title']} - {r['organization']} ({r['url']})"
                    for r in verified_resources
                ]
                self.logger.info(
                    f"Enriched '{skill_gap.skill_name}' with {len(verified_resources)} verified resources"
                )
            else:
                # Keep LLM-generated suggestions as fallback
                self.logger.warning(
                    f"No KB resources for '{skill_gap.skill_name}', keeping LLM suggestions"
                )

        return result
