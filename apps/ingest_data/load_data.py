import os
from typing import Optional, List, Dict, Any
from langchain_core.documents import Document
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LoadData:
    def __init__(
        self,
        embed_model_id: str = "amazon.titan-embed-text-v2:0",
    ) -> None:
        """
        Args:
            embed_model_id: Model embedding
        """
        self.embed_model_id = embed_model_id

        # Base Data Directory
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    def load_itviec(self) -> List[Document]:
        """Load enriched ITviec data."""
        path = os.path.join(
            self.base_dir, "crawler", "data", "raw_itviec", "itviec_enriched.jsonl"
        )
        logger.info(f"Loading ITviec data from: {path}")

        docs = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    if not line.strip():
                        continue
                    try:
                        job = json.loads(line)
                        docs.append(self._parse_itviec_job(job))
                    except json.JSONDecodeError:
                        logger.warning(f"Error decoding JSON at line {idx + 1}")
                    except Exception as e:
                        logger.warning(f"Error parsing job at line {idx+1}: {e}")

            logger.info(f"Loaded {len(docs)} ITviec documents")
            return docs
        except FileNotFoundError:
            logger.error(f"File not found: {path}")
            return []

    def load_topcv(self) -> List[Document]:
        """Load raw TopCV data."""
        path = os.path.join(
            self.base_dir, "crawler", "data", "raw_topcv", "job_details.json"
        )
        logger.info(f"Loading TopCV data from: {path}")

        docs = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

                # Check if it's a list or dict wrapper
                jobs_list = data if isinstance(data, list) else data.get("jobs", [])

                for job in jobs_list:
                    try:
                        docs.append(self._parse_topcv_job(job))
                    except Exception as e:
                        logger.warning(f"Error parsing TopCV job: {e}")

            logger.info(f"Loaded {len(docs)} TopCV documents")
            return docs
        except FileNotFoundError:
            logger.error(f"File not found: {path}")
            return []
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON format in file: {path}")
            return []

    def _sanitize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure all metadata values are valid for ChromaDB (str, int, float, bool)."""
        clean_metadata = {}
        for k, v in metadata.items():
            if v is None:
                clean_metadata[k] = ""
            elif isinstance(v, (str, int, float, bool)):
                clean_metadata[k] = v
            else:
                clean_metadata[k] = str(v)
        return clean_metadata

    def _parse_itviec_job(self, job: Dict[str, Any]) -> Document:
        """Parse structured ITviec job data."""
        title = job.get("job_title") or "Unknown Position"
        company = job.get("company_name") or "Unknown Company"
        skills = ", ".join(
            job.get("skills", []) or job.get("required_skills", []) or []
        )
        location = job.get("location") or "Unknown Location"
        url = job.get("url") or "#"

        # Enriched data often has improved description
        description = job.get("job_description") or job.get("description") or ""

        # Create semantic content block
        page_content = (
            f"Job Title: {title}\n"
            f"Company: {company}\n"
            f"Required Skills: {skills}\n"
            f"Location: {location}\n"
            f"Description: {description}"
        )

        # Extract skills as list for metadata filtering
        skills_list = job.get("skills", []) or job.get("required_skills", []) or []
        # Ensure it's a list
        if isinstance(skills_list, str):
            skills_list = [s.strip() for s in skills_list.split(",") if s.strip()]

        metadata = {
            "title": title,
            "company": company,
            "source": url,
            "location": location,
            "platform": "itviec",
            "skills": ", ".join(
                skills_list
            ),  # Store as comma-separated string for ChromaDB
            "skills_count": len(skills_list),
        }

        return Document(
            page_content=page_content, metadata=self._sanitize_metadata(metadata)
        )

    def _parse_topcv_job(self, job: Dict[str, Any]) -> Document:
        """Parse raw TopCV job data."""
        # Adjust fields based on typical TopCV schema
        title = job.get("title") or job.get("job_title") or "Unknown Position"
        company = job.get("company") or job.get("company_name") or "Unknown Company"

        # TopCV might store skills as text or list
        skills = str(job.get("skills_str") or job.get("skills") or "")
        location = job.get("location") or "Unknown Location"
        url = job.get("url") or job.get("link") or "#"
        description = job.get("description") or job.get("job_description") or ""

        page_content = (
            f"Job Title: {title}\n"
            f"Company: {company}\n"
            f"Required Skills: {skills}\n"
            f"Location: {location}\n"
            f"Description: {description}"
        )

        # Extract skills as list for metadata filtering
        skills_raw = job.get("skills_str") or job.get("skills") or ""
        if isinstance(skills_raw, list):
            skills_list = [str(s).strip() for s in skills_raw if s]
        else:
            skills_list = [s.strip() for s in str(skills_raw).split(",") if s.strip()]

        metadata = {
            "title": title,
            "company": company,
            "source": url,
            "location": location,
            "platform": "topcv",
            "skills": ", ".join(
                skills_list
            ),  # Store as comma-separated string for ChromaDB
            "skills_count": len(skills_list),
        }

        return Document(
            page_content=page_content, metadata=self._sanitize_metadata(metadata)
        )

    def load_all_data(self) -> List[Document]:
        """Load and combine data from all sources."""
        if self.base_dir:
            print("Loading ITviec data")
        itviec_docs = self.load_itviec()
        # topcv_docs = self.load_topcv()
        return itviec_docs  # + topcv_docs


if __name__ == "__main__":
    loader = LoadData()
    all_docs = loader.load_all_data()
    print(f"Total Combined Docs: {len(all_docs)}")
