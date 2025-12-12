from core.agents.base_agent import BaseAgent
from typing import Callable
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from schema.jd import JD
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
                        Ignore any personal information such as address, email, phone, v.v.
                        If the resume is not provided, return 'EMPTY'.
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
            self.logger.error(f"Error while processing extract resume: {e}")

        chain = self.prompt | self.llm.with_structured_output(JD)
        jd = chain.invoke({"jd_content": jd_content})

        return {"jd": jd}
