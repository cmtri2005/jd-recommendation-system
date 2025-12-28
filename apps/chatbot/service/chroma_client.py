from langchain_chroma import Chroma
from src.infra.embeddings.embeddings import embedding_service
from src.config.config import ConfigSingleton
from langchain.schema.document import Document
from typing import List, Tuple, Dict, Any, Optional

config = ConfigSingleton()


def _format_docs(docs: List[Document], scores: List[float] | None = None) -> str:
    if not docs:
        return "Không tìm thấy JD phù hợp."
    for idx, doc in enumerate(docs):
        # Content field
        content = doc.page_content.strip()
        # Metadata field
        metadata: Dict[str, Any] = getattr(doc, "metadata", {}) or {}

        extra_lines: list[str] = []

        # Add all metadata fields
        for key, value in metadata.items():
            clean_key = key.upper().replace("_", " ")
            extra_lines.append(f"[{clean_key}]: {value}")

        if scores:
            extra_lines.append(f"[SCORE]: {scores[idx]:.4f}")

        if extra_lines:
            content = content + "\n\n" + "\n".join(extra_lines)
        return content


class ChromaClientService:
    def __init__(self):
        self.client = None
        self.connection = None
        self.embedding_service = embedding_service

    def connect(self):
        persist_dir = config.CHROMA_PERSIST_DIR
        self.client = Chroma(
            collection_name=config.CHROMA_COLLECTION_NAME,
            persist_directory=str(persist_dir),
            embedding_function=embedding_service,
        )

    def retrieve_docs(
        self,
        query: str,
        top_k: int = 3,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> List[Document]:
        if self.client is None:
            self.connect()

        docs: List[Document] = self.client.similarity_search(
            query, k=top_k, filter=(metadata_filter or None)
        )
        return docs

    def retrieve_vector(
        self,
        query: str,
        top_k: int = 3,
        with_score: bool = False,
        metadata_filter: Optional[Dict[str, Any]] = None,
    ) -> str:
        if self.client is None:
            self.connect()

        if with_score:
            docs_with_scores: List[Tuple[Document, float]] = (
                self.client.similarity_search_with_score(
                    query, k=top_k, filter=(metadata_filter or None)
                )
            )
            try:
                docs, scores = zip(*docs_with_scores)
                return _format_docs(list(docs), list(scores))
            except ValueError:
                return "Không tìm thấy JD phù hợp."
        else:
            docs: List[Document] = self.client.similarity_search(
                query, k=top_k, filter=(metadata_filter or None)
            )
            return _format_docs(docs)
