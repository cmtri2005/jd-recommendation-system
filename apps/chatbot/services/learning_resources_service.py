"""
Learning Resources Knowledge Base Service with ChromaDB.

Uses semantic search to find relevant courses for skills.
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


class LearningResourcesService:
    """Service for retrieving verified learning resources using semantic search."""

    def __init__(self, dataset_path: str, collection_name: str = "learning_resources"):
        """
        Initialize the learning resources service with ChromaDB.

        Args:
            dataset_path: Path to the CSV course dataset
            collection_name: Name of the ChromaDB collection
        """
        self.logger = logging.getLogger(__name__)
        self.dataset_path = dataset_path
        self.collection_name = collection_name

        # Initialize Bedrock embeddings (same as JD retrieval)
        bedrock_embeddings = BedrockEmbeddings(
            model_id=config.BEDROCK_EMBEDDING_MODEL, region_name=config.AWS_REGION
        )
        self.embedding_function = BedrockEmbeddingFunction(bedrock_embeddings)

        # Initialize ChromaDB client using centralized storage path
        chroma_path = os.path.join(config.CHROMA_PERSIST_DIR, "learning_resources")
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
                metadata={"description": "Learning resources for skills"},
            )
            self._ingest_dataset()
        except Exception:
            self.logger.info(
                f"Creating new collection '{collection_name}' with Bedrock Titan embeddings..."
            )
            self.collection = self.client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function,
                metadata={"description": "Learning resources for skills"},
            )
            self._ingest_dataset()

    def _ingest_dataset(self):
        """Load and ingest the course dataset into ChromaDB."""
        if not os.path.exists(self.dataset_path):
            self.logger.error(f"Dataset not found: {self.dataset_path}")
            return

        self.logger.info(f"📚 Ingesting course dataset from {self.dataset_path}")

        documents = []
        metadatas = []
        ids = []

        with open(self.dataset_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            course_count = 0

            for row in reader:
                try:
                    # Extract skills (comma-separated in Skills column)
                    skills_str = row.get("Skills", "")
                    if not skills_str:
                        continue

                    title = row.get("Title", "").strip()
                    url = row.get("course_url", "").strip()

                    # Skip if missing essential fields
                    if not title or not url:
                        continue

                    # Create document: combine title + skills for better semantic search
                    # This helps match both course title and individual skills
                    document = f"{title}. Skills covered: {skills_str}"

                    # Metadata
                    metadata = {
                        "title": title,
                        "organization": row.get("Organization", "").strip(),
                        "url": url,
                        "rating": row.get("Ratings", "0"),
                        "difficulty": row.get("Difficulty", "Unknown"),
                        "type": row.get("Type", "Course"),
                        "skills": skills_str,  # Store original skills string
                        "verified": "true",
                    }

                    # Generate unique ID
                    doc_id = f"course_{course_count}"

                    documents.append(document)
                    metadatas.append(metadata)
                    ids.append(doc_id)

                    course_count += 1

                    # Batch add every 100 courses
                    if len(documents) >= 100:
                        self.collection.add(
                            documents=documents, metadatas=metadatas, ids=ids
                        )
                        self.logger.info(f"  Ingested {course_count} courses...")
                        documents = []
                        metadatas = []
                        ids = []

                except Exception as e:
                    self.logger.warning(f"Error processing row: {e}")
                    continue

        # Add remaining documents
        if documents:
            self.collection.add(documents=documents, metadatas=metadatas, ids=ids)

        self.logger.info(f"✅ Ingested {course_count} courses into ChromaDB")

    def get_resources_for_skill(
        self, skill: str, max_results: int = 3, min_rating: float = 0.0
    ) -> List[Dict]:
        """
        Get verified learning resources for a specific skill using semantic search.

        Args:
            skill: Skill name to search for
            max_results: Maximum number of resources to return
            min_rating: Minimum course rating filter

        Returns:
            List of resource dictionaries with verified=True
        """
        try:
            # Semantic search in ChromaDB
            results = self.collection.query(
                query_texts=[skill],
                n_results=max_results * 2,  # Get more to filter by rating
                include=["metadatas", "distances"],
            )

            if not results or not results["metadatas"] or not results["metadatas"][0]:
                self.logger.info(f"No resources found for skill: {skill}")
                return []

            # Convert to resource dicts
            resources = []
            for metadata, distance in zip(
                results["metadatas"][0], results["distances"][0]
            ):
                # Filter by rating
                try:
                    rating = float(metadata.get("rating", 0))
                    if rating < min_rating:
                        continue
                except (ValueError, TypeError):
                    pass

                resource = {
                    "title": metadata.get("title", ""),
                    "organization": metadata.get("organization", ""),
                    "url": metadata.get("url", ""),
                    "rating": metadata.get("rating", "0"),
                    "difficulty": metadata.get("difficulty", "Unknown"),
                    "type": metadata.get("type", "Course"),
                    "verified": True,  # All dataset entries are verified
                    "relevance_score": 1.0 - distance,  # Convert distance to similarity
                }

                resources.append(resource)

                if len(resources) >= max_results:
                    break

            self.logger.debug(f"Found {len(resources)} resources for '{skill}'")
            return resources

        except Exception as e:
            self.logger.error(f"Error querying ChromaDB: {e}")
            return []

    def search_resources(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Full-text semantic search across all courses.

        Args:
            query: Search query
            max_results: Maximum results to return

        Returns:
            List of matching resources
        """
        return self.get_resources_for_skill(query, max_results=max_results)

    def get_stats(self) -> Dict[str, int]:
        """Get statistics about the knowledge base."""
        try:
            count = self.collection.count()
            return {"total_courses": count, "collection_name": self.collection_name}
        except Exception as e:
            self.logger.error(f"Error getting stats: {e}")
            return {"total_courses": 0, "collection_name": self.collection_name}


# Singleton instance
_service_instance: Optional[LearningResourcesService] = None


def get_learning_resources_service(
    dataset_path: Optional[str] = None,
) -> LearningResourcesService:
    """
    Get or create singleton instance of LearningResourcesService.

    Args:
        dataset_path: Path to dataset (optional, uses default if not provided)

    Returns:
        LearningResourcesService instance
    """
    global _service_instance

    if _service_instance is None:
        if dataset_path is None:
            # Default path
            dataset_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                "data",
                "rcm_course_dataset.csv",
            )

        _service_instance = LearningResourcesService(dataset_path)

    return _service_instance
