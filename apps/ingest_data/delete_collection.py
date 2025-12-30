import chromadb
import sys
from pathlib import Path

# Path to vector store
PERSIST_DIRECTORY = "../chatbot/infra/vector_stores/storage"
COLLECTION_NAME = "rag-jd-rcm"


def delete_specific_collection():
    print(f"Attempting to delete collection: {COLLECTION_NAME}")
    try:
        path = Path(PERSIST_DIRECTORY).resolve()
        print(f"Storage Path: {path}")

        client = chromadb.PersistentClient(path=str(path))

        try:
            client.delete_collection(COLLECTION_NAME)
            print(f"✅ Successfully deleted collection '{COLLECTION_NAME}'")
        except ValueError:
            print(f"⚠️ Collection '{COLLECTION_NAME}' does not exist.")
        except Exception as e:
            print(f"❌ Error deleting collection: {e}")

    except Exception as ex:
        print(f"❌ System Error: {ex}")


if __name__ == "__main__":
    delete_specific_collection()
