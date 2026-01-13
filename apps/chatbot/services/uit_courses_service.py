"""
UIT Courses Knowledge Base Service with ChromaDB.

Uses semantic search to find relevant UIT courses for skills.
"""

import csv
import os
import logging
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from langchain_aws import BedrockEmbeddings
from config.config import config


class BedrockEmbeddingFunction:
    """Wrapper to make BedrockEmbeddings compatible with ChromaDB interface."""

    def __init__(self, bedrock_embeddings: BedrockEmbeddings):
        self.bedrock_embeddings = bedrock_embeddings

    def __call__(self, input: List[str]) -> List[List[float]]:
        """Embed documents using Bedrock.

        Args:
            input: List of texts to embed

        Returns:
            List of embeddings
        """
        return self.bedrock_embeddings.embed_documents(input)


class UITCoursesService:
    """Service for retrieving UIT courses using semantic search."""

    def __init__(self, dataset_path: str, collection_name: str = "uit_courses"):
        """
        Initialize the UIT courses service with ChromaDB.

        Args:
            dataset_path: Path to the CSV course dataset
            collection_name: Name of the ChromaDB collection
        """
        self.logger = logging.getLogger(__name__)
        self.dataset_path = dataset_path
        self.collection_name = collection_name

        # Set AWS credentials in environment FIRST (before BedrockEmbeddings init)
        import os

        os.environ["AWS_ACCESS_KEY_ID"] = config.AWS_ACCESS_KEY_ID
        os.environ["AWS_SECRET_ACCESS_KEY"] = config.AWS_SECRET_ACCESS_KEY
        os.environ["AWS_DEFAULT_REGION"] = config.AWS_REGION

        # Initialize Bedrock embeddings (boto3 will now find credentials in env)
        bedrock_embeddings = BedrockEmbeddings(
            model_id=config.BEDROCK_EMBEDDING_MODEL, region_name=config.AWS_REGION
        )
        self.embedding_function = BedrockEmbeddingFunction(bedrock_embeddings)

        # Initialize ChromaDB client using ISOLATED storage path
        chroma_path = os.path.join(config.CHROMA_PERSIST_DIR, "..", "uit_courses_db")
        self.client = chromadb.PersistentClient(path=chroma_path)

        # Get or create collection with Bedrock embeddings
        try:
            self.collection = self.client.get_collection(
                name=collection_name, embedding_function=self.embedding_function
            )
            self.logger.info(f"✅ Loaded existing collection '{collection_name}'")

            # Check if collection is empty (edge case: created but not ingested)
            if self.collection.count() == 0:
                self.logger.warning(
                    f"Collection '{collection_name}' is empty, ingesting dataset..."
                )
                self._ingest_dataset()
        except ValueError as e:
            # Collection exists but with different embedding function
            self.logger.warning(
                f"Collection exists with incompatible embedding function, recreating..."
            )
            try:
                self.client.delete_collection(name=collection_name)
            except Exception:
                pass

            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "UIT courses for skills"},
            )
            self._ingest_dataset()
        except Exception:
            self.logger.info(
                f"Creating new collection '{collection_name}' with Bedrock Titan embeddings..."
            )
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "UIT courses for skills"},
            )
            self._ingest_dataset()

    def _ingest_dataset(self):
        """Load and ingest the UIT course dataset into ChromaDB."""
        if not os.path.exists(self.dataset_path):
            self.logger.error(f"Dataset not found: {self.dataset_path}")
            return

        self.logger.info(f"📚 Ingesting UIT course dataset from {self.dataset_path}")

        documents = []
        metadatas = []
        ids = []

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            course_count = 0

            for row in reader:
                try:
                    # Extract fields from UIT dataset
                    course_name = row.get("Tên môn học", "").strip()
                    department = row.get("Khoa", "").strip()
                    major = row.get("Ngành", "").strip()
                    skills_str = row.get("Hard skills", "").strip()

                    # Skip if missing essential fields
                    if not course_name or not skills_str:
                        continue

                    # Create document: combine course name + department + major + skills
                    # This helps semantic search match both course content and skills
                    document = f"{course_name}. Khoa: {department}. Ngành: {major}. Kỹ năng: {skills_str}"

                    # Metadata
                    metadata = {
                        "course_name": course_name,
                        "department": department,
                        "major": major,
                        "skills": skills_str,
                        "source": "UIT",
                        "verified": "true",
                    }

                    # Generate unique ID
                    doc_id = f"uit_course_{course_count}"

                    documents.append(document)
                    metadatas.append(metadata)
                    ids.append(doc_id)

                    course_count += 1

                    # Batch add every 100 courses
                    if len(documents) >= 100:
                        self.collection.add(
                            documents=documents, metadatas=metadatas, ids=ids
                        )
                        self.logger.info(f"  Ingested {course_count} UIT courses...")
                        documents = []
                        metadatas = []
                        ids = []

                except Exception as e:
                    self.logger.warning(f"Error processing row: {e}")
                    continue

        # Add remaining documents
        if documents:
            self.collection.add(documents=documents, metadatas=metadatas, ids=ids)

        self.logger.info(f"✅ Ingested {course_count} UIT courses into ChromaDB")

    def get_courses_for_skill(self, skill: str, max_results: int = 3) -> List[Dict]:
        """
        Get UIT courses for a specific skill using semantic search.

        Args:
            skill: Skill name to search for
            max_results: Maximum number of courses to return

        Returns:
            List of course dictionaries with verified=True
        """
        try:
            # Semantic search in ChromaDB
            results = self.collection.query(
                query_texts=[skill],
                n_results=max_results,
                include=["metadatas", "distances"],
            )

            if not results or not results["metadatas"] or not results["metadatas"][0]:
                self.logger.info(f"No UIT courses found for skill: {skill}")
                return []

            # Convert to course dicts
            courses = []
            for metadata, distance in zip(
                results["metadatas"][0], results["distances"][0]
            ):
                course = {
                    "course_name": metadata.get("course_name", ""),
                    "department": metadata.get("department", ""),
                    "major": metadata.get("major", ""),
                    "skills": metadata.get("skills", ""),
                    "source": "UIT",
                    "verified": True,
                    "relevance_score": 1.0 - distance,  # Convert distance to similarity
                }

                courses.append(course)

            self.logger.debug(f"Found {len(courses)} UIT courses for '{skill}'")
            return courses

        except Exception as e:
            self.logger.error(f"Error querying ChromaDB: {e}")
            return []

    def search_courses(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Full-text semantic search across all UIT courses.

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            List of matching courses
        """
        return self.get_courses_for_skill(query, max_results=max_results)

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the knowledge base."""
        try:
            count = self.collection.count()
            return {"total_courses": count, "collection_name": self.collection_name}
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {"total_courses": 0, "collection_name": self.collection_name}


# Singleton instance
_service_instance: Optional[UITCoursesService] = None


def get_uit_courses_service(
    dataset_path: Optional[str] = None,
) -> UITCoursesService:
    """
    Get or create singleton instance of UITCoursesService.

    Args:
        dataset_path: Path to dataset (optional, uses default if not provided)

    Returns:
        UITCoursesService instance
    """
    global _service_instance

    if _service_instance is None:
        if dataset_path is None:
            # Default path
            dataset_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data",
                "course_uit_dataset.csv",
            )

        _service_instance = UITCoursesService(dataset_path)

    return _service_instance
