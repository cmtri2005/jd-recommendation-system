from core.agents.base_agent import BaseAgent
from typing import Callable
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from schema.jd import JD, JDList
from tools.document_loader import docx_loader, pdf_loader
from core.factories.llm_factory import LLMFactory


class JDExtractAgent(BaseAgent):
    def __init__(self, name: str, llm: BaseChatModel, tools: list[Callable]):
        super().__init__(name, llm, tools)
        self.name = "jd_agent"
        self.prompt = self.jd_extract_chat_prompt_template()

    def jd_extract_chat_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate(
            [
                (
                    "system",
                    """
                        You are a jd assistant.
                        Your task is to analyze the job description between triple backticks and extract structured information from it.
                        The document may contain ONE or MULTIPLE job descriptions. If there are multiple job descriptions (separated by different job titles, sections, or clear boundaries), extract ALL of them.
                        For each job description, you must extract ALL fields including:
                        - job_summary: A brief summary of the job description
                        - require_hard_skills: All required hard/technical skills mentioned
                        - optional_hard_skills: All optional/preferred hard/technical skills mentioned
                        - required_soft_skills: All required soft skills mentioned
                        - optional_soft_skills: All optional soft skills mentioned
                        - required_work_experiences: All required work experiences, job roles, or industry experience mentioned
                        - optional_work_experiences: All optional/preferred work experiences mentioned
                        - required_educations: All required educational backgrounds mentioned
                        - optional_educations: All optional educational backgrounds mentioned
                        - required_years_of_experience: The number of years of experience required
                        
                        Make sure to extract ALL information from the job description. Pay special attention to work experience requirements, skills (both hard and soft), and education requirements.
                        Ignore any personal information such as address, email, phone, v.v.
                        If the job description is not provided, return an empty list.
                    """,
                ),
                (
                    "user",
                    "Please analyzing the following resume: ```{jd_content}```",
                ),
            ]
        )

    def extract_jd(self, jd_path: str):
        jd_content = ""
        try:
            if "docx" in jd_path.split("."):
                self.logger.info(f"Processing DOCX jd: {jd_path}")
                jd_content = docx_loader.invoke(jd_path)
            elif "pdf" in jd_path.split("."):
                self.logger.info(f"Processing PDF jd: {jd_path}")
                jd_content = pdf_loader.invoke(jd_path)
        except Exception as e:
            jd_content = ""
            self.logger.error(f"Error while processing extract jd: {e}")

        chain = self.prompt | self.llm.with_structured_output(JDList)
        jd_list_result = chain.invoke({"jd_content": jd_content})

        return {"jds": jd_list_result.jds, "count": len(jd_list_result.jds)}
