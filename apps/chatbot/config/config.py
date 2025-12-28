import os
import threading
from dotenv import dotenv_values
from pathlib import Path


PROJECT_ROOT = Path(__file__).parent.parent


class ConfigSingleton:
    __instance = None
    __lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            with cls.__lock:
                if cls.__instance is None:
                    cls.__instance = super().__new__(cls)
                    cls.__instance.__initialize()
        return cls.__instance

    def __initialize(self) -> None:
        env = {**dotenv_values(".env"), **os.environ}

        # LLM
        self.AWS_ACCESS_KEY_ID = env.get("AWS_ACCESS_KEY_ID", "")
        self.AWS_SECRET_ACCESS_KEY = env.get("AWS_SECRET_ACCESS_KEY", "")
        self.AWS_REGION = env.get("AWS_REGION", "us-east-1")
        self.BEDROCK_MODEL_REGION = env.get("BEDROCK_MODEL_REGION", "us-east-1")
        self.BEDROCK_EMBEDDING_MODEL = env.get(
            "BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v2:0"
        )
        self.BEDROCK_LLM_MODEL = env.get(
            "BEDROCK_LLM_MODEL", "anthropic.claude-3-5-sonnet-20240620-v1:0"
        )

        # GROQ
        self.GROQ_API_KEY = env.get("GROQ_API_KEY", "")
        self.GROQ_MODEL = env.get("GROQ_MODEL", "llama-3.3-70b-versatile")

        # Vector Store
        self.DATASET_NAME: str = os.getenv(
            "DATASET_NAME", "jd-rcm"
        )  # Dynamic from environment
        self.CHROMA_COLLECTION_NAME: str = f"rag-{self.DATASET_NAME}"
        self.CHROMA_PERSIST_DIR: str = str(
            PROJECT_ROOT / "infra" / "vector_stores" / "storage"
        )


config = ConfigSingleton()
