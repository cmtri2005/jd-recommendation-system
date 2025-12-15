from typing import TypedDict, Required, NotRequired
from enum import Enum
from langchain_core.language_models.chat_models import BaseChatModel


class LLMFactory:
    """LLM config"""

    class LLMConfig(TypedDict):
        model_name: Required[str]
        api_key: Required[str]
        api_endpoint: NotRequired[str]
        max_completion_tokens: NotRequired[int]
        temperature: NotRequired[float]
        max_retrieves: NotRequired[float]
        timeout: NotRequired[float]

    class Provider(Enum):
        GEMINI = "gemini"
        GROQ = "groq"

    @staticmethod
    def create_llm(llm_provider: Provider, config: LLMConfig) -> BaseChatModel:
        if llm_provider == LLMFactory.Provider.GEMINI:
            from langchain_google_genai import ChatGoogleGenerativeAI

            kwargs = {
                "model": config["model_name"],
                "google_api_key": config["api_key"],
            }

            if "max_completion_tokens" in config:
                kwargs["max_output_tokens"] = config["max_completion_tokens"]
            if "temperature" in config:
                kwargs["temperature"] = config["temperature"]
            if "timeout" in config:
                kwargs["timeout"] = config["timeout"]

            return ChatGoogleGenerativeAI(**kwargs)

        if llm_provider == LLMFactory.Provider.GROQ:
            from langchain_groq import ChatGroq

            kwargs = {
                "model": config["model_name"],
                "groq_api_key": config["api_key"],
            }

            if "max_completion_tokens" in config:
                kwargs["max_tokens"] = config["max_completion_tokens"]
            if "temperature" in config:
                kwargs["temperature"] = config["temperature"]
            if "max_retries" in config:
                kwargs["max_retries"] = config["max_retries"]
            if "timeout" in config:
                kwargs["timeout"] = config["timeout"]

            return ChatGroq(**kwargs)

        if llm_provider not in LLMFactory.Provider:
            raise ValueError(
                f"Unsupported LLM provider: {llm_provider}. Supported providers are: {list(LLMFactory.Provider)}"
            )
