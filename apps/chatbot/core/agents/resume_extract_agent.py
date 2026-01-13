from core.agents.base_agent import BaseAgent
from typing import Callable
import traceback
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from schemas.resume import Resume
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
                        
                        IMPORTANT: Generate ALL extracted text in Vietnamese language.
                    """,

                ),
                (
                    "user",
                    "Please analyzing the following resume: ```{resume_content}```",
                ),
            ]
        )

    def extract_resume(self, resume_path: str):
        """Extract resume information from file.

        Args:
            resume_path: Path to resume file (PDF or DOCX)

        Returns:
            Dict containing extracted Resume object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type is unsupported
            RuntimeError: If extraction fails
        """
        try:
            if "docx" in resume_path.split("."):
                self.logger.info(f"Processing DOCX resume: {resume_path}")
                resume_content = docx_loader.invoke(resume_path)
            elif "pdf" in resume_path.split("."):
                self.logger.info(f"Processing PDF resume: {resume_path}")
                resume_content = pdf_loader.invoke(resume_path)
            else:
                raise ValueError(f"Unsupported file type: {resume_path}")
        except FileNotFoundError:
            self.logger.error(f"File not found: {resume_path}")
            raise
        except ValueError:
            # Re-raise ValueError for unsupported file types
            raise
        except Exception as e:
            self.logger.error(
                f"Error while processing resume file: {e}\n{traceback.format_exc()}"
            )
            raise RuntimeError(f"Failed to extract resume from {resume_path}") from e

        # Extract structured data using LLM
        try:
            chain = self.prompt | self.llm.with_structured_output(Resume)
            resume = chain.invoke({"resume_content": resume_content})
            self.logger.info(f"Successfully extracted resume from {resume_path}")
            return {"resume": resume}
        except Exception as e:
            self.logger.error(
                f"LLM extraction failed for {resume_path}: {e}\n{traceback.format_exc()}"
            )
            raise RuntimeError(f"Failed to parse resume content with LLM") from e
