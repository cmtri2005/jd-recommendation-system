from core.agents.base_agent import BaseAgent
from typing import Callable
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from schema.resume import Resume
from tools.document_loader import docx_loader, pdf_loader
from core.factories.llm_factory import LLMFactory


class ResumeExtractAgent(BaseAgent):
    def __init__(self, name: str, llm: BaseChatModel, tools: list[Callable]):
        super().__init__(name, llm, tools)
        self.name = "resume_agent"
        self.prompt = self.resume_extract_chat_prompt_template()

    def resume_extract_chat_prompt_template(self) -> ChatPromptTemplate:
        return ChatPromptTemplate(
            [
                (
                    "system",
                    """
                        You are a resume assistant.
                        Your task is to analyze the resume between triple backticks and extract structured information from it.
                        Ignore any personal information such as address, email, phone, v.v.
                        If the resume is not provided, return 'EMPTY'.
                    """,
                ),
                (
                    "user",
                    "Please analyzing the following resume: ```{resume_content}```",
                ),
            ]
        )

    def extract_resume(self, resume_path: str):
        resume_content = ""
        try:
            if "docx" in resume_path.split("."):
                self.logger.info(f"Processing DOCX resume: {resume_path}")
                resume_content = docx_loader.invoke(resume_path)
            elif "pdf" in resume_path.split("."):
                self.logger.info(f"Processing PDF resume: {resume_path}")
                resume_content = pdf_loader.invoke(resume_path)
        except Exception as e:
            resume_content = ""
            self.logger.error(f"Error while processing extract resume: {e}")

        chain = self.prompt | self.llm.with_structured_output(Resume)
        resume = chain.invoke({"resume_content": resume_content})

        return {"resume": resume}
