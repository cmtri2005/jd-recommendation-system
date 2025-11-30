import os
from logging import Logger
from core.agents.resume_extract_agent import ResumeExtractAgent
from core.factories.llm_factory import LLMFactory
from tools.document_loader import docx_loader, pdf_loader
from dotenv import load_dotenv

load_dotenv()

class Orchestrator:
    def __init__(self):
        model_name = os.environ["MODEL_NAME"]
        api_key = os.environ["API_KEY"]
        self.llm = LLMFactory.create_llm(
            llm_provider=LLMFactory.Provider.GEMINI,
            config=LLMFactory.LLMConfig(model_name=model_name, api_key=api_key),
        )
        self.tools = ["docx_loader", "pdf_loader"]
