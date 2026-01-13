from typing import Annotated, Literal, TypedDict, Sequence, Callable
from langgraph.graph import END, START, StateGraph, MessagesState
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from core.agents.base_agent import BaseAgent
from schemas.evaluation import EvaluationResult
from services.learning_resources_service import get_learning_resources_service
from services.uit_courses_service import get_uit_courses_service
from dotenv import load_dotenv


load_dotenv()


class EvaluationAgent(BaseAgent):
    """Agent for evaluation matching score between resume and jd"""

    def __init__(self, name: str, llm: BaseChatModel, tools: list[Callable]):
        super().__init__(name, llm, tools)
        self.name = "evaluation_agent"
        self.prompt = self.evaluation_agent_chat_prompt_template()
        # Initialize learning resources services
        self.learning_resources = get_learning_resources_service()
        self.uit_courses = get_uit_courses_service()

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
                       - **category** must be in ENGLISH using one of: "Hard Skills", "Soft Skills", "Work Experience", "Years of Experience", "Education", "Extras"
                       - **details** should be in Vietnamese
                    4. **weaknesses**: Array of {{category, details}} for gaps
                       - **category** must be in ENGLISH using one of: "Hard Skills", "Soft Skills", "Work Experience", "Years of Experience", "Education", "Extras"
                       - **details** should be in Vietnamese
                    5. **missing_hard_skills**: Array of {{skill_name, importance, learning_resources[]}} 
                    6. **summary**: 3-4 line summary covering strengths and missing areas (in Vietnamese)
                    7. **recommendation**: "suitable" if score >= 60, else "not_suitable"
                    8. **recommendation_reason**: REQUIRED - Detailed explanation of why suitable/not suitable (in Vietnamese)
                    
                    Example JSON structure:
                    {{
                      "total_score": 67,
                      "score_breakdown": {{
                        "hard_skills_score": 20,
                        "soft_skills_score": 4,
                        "work_experience_score": 25,
                        "years_of_experience_score": 10,
                        "education_score": 5,
                        "extras_score": 3
                      }},
                      "strengths": [
                        {{"category": "Hard Skills", "details": "Ứng viên có kinh nghiệm vững về Python và Django"}},
                        {{"category": "Work Experience", "details": "Có 3 năm kinh nghiệm làm Backend Developer"}}
                      ],
                      "weaknesses": [
                        {{"category": "Hard Skills", "details": "Thiếu kinh nghiệm về AWS và Docker"}}
                      ],
                      "missing_hard_skills": [
                        {{"skill_name": "AWS", "importance": "critical", "learning_resources": []}}
                      ],
                      "summary": "Ứng viên có nền tảng vững về Python...",
                      "recommendation": "suitable",
                      "recommendation_reason": "Ứng viên phù hợp với vị trí này vì..."
                    }}
                    
                    IMPORTANT: 
                    - Ensure total_score equals the sum of all breakdown scores!
                    - For strengths/weaknesses: **category** field MUST be in English, **details** field in Vietnamese
                    - Generate all OTHER text fields (summary, recommendation_reason, skill details, etc.) in Vietnamese language.
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
        """Enrich skill gaps with verified learning resources from both online and UIT courses.

        Queries both online course dataset and UIT course dataset to provide comprehensive
        learning recommendations. Combines both sources with clear labeling.

        Args:
            result: Original evaluation result from LLM

        Returns:
            Evaluation result with enriched learning resources (online + UIT)
        """
        if not result.missing_hard_skills:
            self.logger.info("🔍 No missing skills to enrich")
            return result

        self.logger.info(
            f"🔍 Enriching {len(result.missing_hard_skills)} missing skills with online + UIT resources..."
        )

        for skill_gap in result.missing_hard_skills:
            all_resources = []

            # 1. Get online courses (Coursera, Google, etc.)
            online_resources = self.learning_resources.get_resources_for_skill(
                skill_gap.skill_name,
                max_results=2,
                min_rating=4.0,
            )

            # 2. Get UIT courses
            uit_resources = self.uit_courses.get_courses_for_skill(
                skill_gap.skill_name,
                max_results=2,
            )

            # Format online courses
            if online_resources:
                for r in online_resources:
                    all_resources.append(
                        f"[Online] {r['title']} - {r['organization']} ({r['url']})"
                    )
                self.logger.info(
                    f"Found {len(online_resources)} online courses for '{skill_gap.skill_name}'"
                )

            # Format UIT courses
            if uit_resources:
                for r in uit_resources:
                    all_resources.append(
                        f"[UIT] {r['course_name']} - {r['department']} (Ngành: {r['major']})"
                    )
                self.logger.info(
                    f"Found {len(uit_resources)} UIT courses for '{skill_gap.skill_name}'"
                )

            # Update skill gap with combined resources or keep LLM suggestions
            if all_resources:
                skill_gap.learning_resources = all_resources
                self.logger.info(
                    f"✅ Enriched '{skill_gap.skill_name}' with {len(all_resources)} total resources"
                )
            else:
                # Keep LLM-generated suggestions as fallback
                self.logger.warning(
                    f"⚠️ No verified resources for '{skill_gap.skill_name}', keeping LLM suggestions"
                )

        return result
