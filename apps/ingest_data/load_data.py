import os
from typing import Optional
from langchain_core.documents import Document
import json


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

    def load_data(self, path: Optional[str] = None) -> list[Document]:
        if path is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            path = os.path.join(base_dir, "crawler", "data", "jobs_raw.jsonl")
        docs = []
        try:
            with open(path, "r", encoding="utf-8") as f:
                for idx, line in enumerate(f):
                    if not line.strip():
                        continue
                    try:
                        job = json.loads(line)

                        # Construct content from relevant fields
                        title = job.get("job_title", "")
                        skills = ", ".join(job.get("required_skills", []))
                        exp = job.get("your_skills_experience", "")
                        desc = job.get("job_description", "")

                        # Combine fields for embedding
                        page_content = f"Title: {title}\nSkills: {skills}\nExperience Requirements: {exp}\nDescription: {desc}"

                        metadata = {
                            "source": job.get("url", ""),
                            "title": title,
                        }

                        docs.append(
                            Document(page_content=page_content, metadata=metadata)
                        )

                    except json.JSONDecodeError:
                        print(f"Error decoding JSON at line {idx + 1}")
                        continue

            print(f"Total documents created: {len(docs)}")
            return docs

        except FileNotFoundError:
            print(f"File not found: {path}")
            return []


if __name__ == "__main__":
    loader = LoadData()
    docs = loader.load_data()
    print(docs)
