from langchain_core.documents import Document
from langchain_chroma import Chroma
from langchain_aws import BedrockEmbeddings
from langchain_community.vectorstores.utils import filter_complex_metadata
from uuid import uuid4


class DocumentEmbedder:
    def __init__(
        self,
        model_id: str = "amazon.titan-embed-text-v2:0",
        region_name: str = "us-east-1",
    ):
        print(
            f"Initializing Bedrock embeddings for model: {model_id} (region: {region_name})"
        )
        self.embeddings = BedrockEmbeddings(model_id=model_id, region_name=region_name)

    def document_embedding_vectorstore(
        self, split_docs: list[Document], collection_name: str, persist_directory: str
    ):
        """
        Generate embeddings for the documents and store them in a vector store.

        Args:
            split (list[Document]): List of Document objects with content.
            collection_name (str): Name of the Chroma collection.
            persist_directory (str): Directory to persist the vector store.
        """
        print("---Initializing Chroma vector store---")

        # 1. Load the Chroma collection
        vectordb = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=persist_directory,
            collection_metadata={"dimension": 1024, "hnsw:space": "cosine"},
        )
        # 2. Generate unique ID for each document chunk
        uuids = [str(uuid4()) for _ in split_docs]

        # 3. Add documents to the vector store
        print(f"Adding {len(split_docs)} documents to the vector store")
        vectordb.add_documents(
            documents=split_docs,
            ids=uuids,
        )
        return vectordb
