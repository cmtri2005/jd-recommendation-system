import sys
import traceback
from pathlib import Path
from load_data import LoadData
from dotenv import load_dotenv

load_dotenv()

from embed_and_store import DocumentEmbedder


DATA_PATH = "../crawler/data/jobs_raw.jsonl"
COLLECTION_NAME = "rag-jd-rcm"
PERSIST_DIRECTORY = "../chatbot/infra/vector_stores/storage"


def main():
    print("=" * 80)
    print("Starting Data Ingestion Pipeline")
    print("=" * 80)

    print("\nLoading and chunking documents...")
    loader = LoadData()
    docs = loader.load_data(path=DATA_PATH)
    print(f"Successfully loaded {len(docs)} documents")

    print("\nCreating embeddings and storing in vector database...")
    embedder = DocumentEmbedder()

    persist_path = Path(PERSIST_DIRECTORY)
    persist_path.mkdir(parents=True, exist_ok=True)
    vectordb = embedder.document_embedding_vectorstore(
        split_docs=docs,
        collection_name=COLLECTION_NAME,
        persist_directory=str(persist_path),
    )

    print(f"Successfully stored documents in Chroma collection: {COLLECTION_NAME}")
    print(f"Persist directory: {persist_path.absolute()}")

    print("\nChecking vector store...")
    doc_count = vectordb._collection.count()
    print(f"Total documents in vector store: {doc_count}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\nError during ingestion: {str(e)}", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
