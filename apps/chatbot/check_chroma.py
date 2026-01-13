import chromadb
from pathlib import Path
from config.config import config


def list_collections():
    persist_dir = config.CHROMA_PERSIST_DIR
    print(f"Checking ChromaDB at: {persist_dir}")

    if not Path(persist_dir).exists():
        print("ChromaDB directory does not exist.")
        return

    try:
        client = chromadb.PersistentClient(path=persist_dir)
        collections = client.list_collections()

        print(f"\nFound {len(collections)} collections:")
        for col in collections:
            print(f"- {col.name} (Count: {col.count()})")

    except Exception as e:
        print(f"Error accessing ChromaDB: {e}")


if __name__ == "__main__":
    list_collections()
