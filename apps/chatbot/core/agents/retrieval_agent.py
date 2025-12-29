import os
from typing import List, Callable, Dict, Any, Optional
from langchain_community.vectorstores import Chroma
from langchain_aws import BedrockEmbeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate
from schemas.retrieval import Retrieval
from config.config import config
from core.agents.base_agent import BaseAgent


class RetrievalAgent(BaseAgent):
    """An agent to retrieve from vector database"""

    def __init__(self, name: str, llm: BaseChatModel, tools: List[Callable]):
        super().__init__(name, llm, tools)
        self.name = "retrieval_agent"

        # Initialize Vector Store
        embedding_function = BedrockEmbeddings(
            model_id=config.BEDROCK_EMBEDDING_MODEL,
            region_name=config.BEDROCK_MODEL_REGION,
        )

        self.vectorstore = Chroma(
            persist_directory=config.CHROMA_PERSIST_DIR,
            embedding_function=embedding_function,
            collection_name=config.CHROMA_COLLECTION_NAME,
        )
        self.retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})

    def retrieve(self, query: str, k: int = 5) -> List[str]:
        """Retrieve relevant documents based on query with similarity scores"""
        # Use similarity_search_with_score to get distance scores
        docs_with_scores = self.vectorstore.similarity_search_with_score(query, k=k)

        results = []
        for doc, distance in docs_with_scores:
            content = doc.page_content
            metadata = doc.metadata
            source = metadata.get("source", "Unknown Source")
            title = metadata.get("title", "Unknown Title")
            similarity_score = 1 / (1 + distance)
            match_percentage = similarity_score * 100

            results.append(
                f"🎯 Match Score: {match_percentage:.1f}%\n"
                f"Title: {title}\n"
                f"Source: {source}\n"
                f"Content Sample: {content[:200]}..."
            )
        return results
