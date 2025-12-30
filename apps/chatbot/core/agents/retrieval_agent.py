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
    """An agent to retrieve from vector database with skill-based filtering"""

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

    def calculate_skill_match(
        self, resume_skills: List[str], jd_skills_str: str
    ) -> Dict[str, Any]:
        """
        Calculate skill match percentage between resume and JD.

        Args:
            resume_skills: List of skills from the resume
            jd_skills_str: Comma-separated string of JD required skills from metadata

        Returns:
            Dict with match_percentage, matched_skills, missing_skills
        """
        if not resume_skills or not jd_skills_str:
            return {
                "match_percentage": 0.0,
                "matched_skills": [],
                "missing_skills": [],
            }

        # Parse JD skills
        jd_skills = [s.strip().lower() for s in jd_skills_str.split(",") if s.strip()]
        resume_skills_lower = [s.strip().lower() for s in resume_skills if s.strip()]

        if not jd_skills:
            return {
                "match_percentage": 0.0,
                "matched_skills": [],
                "missing_skills": [],
            }

        # Find matches
        matched = []
        missing = []

        for jd_skill in jd_skills:
            # Check for exact match or substring match
            is_matched = False
            for resume_skill in resume_skills_lower:
                # Match if either skill contains the other (handles variations like "React" vs "React.js")
                if jd_skill in resume_skill or resume_skill in jd_skill:
                    matched.append(jd_skill)
                    is_matched = True
                    break

            if not is_matched:
                missing.append(jd_skill)

        # Calculate match percentage
        match_percentage = (len(matched) / len(jd_skills) * 100) if jd_skills else 0.0

        return {
            "match_percentage": match_percentage,
            "matched_skills": matched,
            "missing_skills": missing,
        }

    def retrieve(
        self,
        query: str,
        k: int = 5,
        resume_skills: Optional[List[str]] = None,
        min_skill_match: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents with hybrid ranking (vector similarity + skill match).

        Args:
            query: Search query
            k: Number of results to return
            resume_skills: List of skills from resume for filtering/re-ranking
            min_skill_match: Minimum skill match percentage (0-100) to include result

        Returns:
            List of result dictionaries with scores and metadata
        """
        # Retrieve more candidates for filtering
        retrieval_k = k * 2 

        # Use similarity_search_with_score to get distance scores
        docs_with_scores = self.vectorstore.similarity_search_with_score(
            query, k=retrieval_k
        )

        results = []
        for doc, distance in docs_with_scores:
            content = doc.page_content
            metadata = doc.metadata
            source = metadata.get("source", "Unknown Source")
            title = metadata.get("title", "Unknown Title")
            jd_skills_str = metadata.get("skills", "")

            # Calculate vector similarity score
            similarity_score = 1 / (1 + distance)
            vector_match_pct = similarity_score * 100

            # Calculate skill match if resume skills provided
            skill_match_data = {
                "match_percentage": 0.0,
                "matched_skills": [],
                "missing_skills": [],
            }
            if resume_skills:
                skill_match_data = self.calculate_skill_match(
                    resume_skills, jd_skills_str
                )

            skill_match_pct = skill_match_data["match_percentage"]

            # Apply minimum skill match filter ONLY if resume skills are provided
            if (
                resume_skills
                and min_skill_match > 0
                and skill_match_pct < min_skill_match
            ):
                continue

            # Calculate hybrid score (weighted combination)
            # 60% vector similarity + 40% skill match
            hybrid_score = (vector_match_pct * 0.6) + (skill_match_pct * 0.4)

            result = {
                "title": title,
                "source": source,
                "content": content,
                "metadata": metadata,
                "vector_match": vector_match_pct,
                "skill_match": skill_match_pct,
                "hybrid_score": hybrid_score,
                "matched_skills": skill_match_data["matched_skills"],
                "missing_skills": skill_match_data["missing_skills"],
            }
            results.append(result)

        # Sort by hybrid score (descending)
        results.sort(key=lambda x: x["hybrid_score"], reverse=True)

        # Return top k results
        return results[:k]

    def format_results_for_display(self, results: List[Dict[str, Any]]) -> List[str]:
        """
        Format results for display in the chat UI.

        Args:
            results: List of result dictionaries from retrieve()

        Returns:
            List of formatted strings
        """
        formatted = []
        for result in results:
            matched_skills_str = ", ".join(
                result["matched_skills"][:5]
            )  # Show top 5 matched
            missing_skills_str = ", ".join(
                result["missing_skills"][:3]
            )  # Show top 3 missing

            formatted_result = (
                f"🎯 Hybrid Score: {result['hybrid_score']:.1f}% "
                f"(Vector: {result['vector_match']:.1f}%, Skills: {result['skill_match']:.1f}%)\n"
                f"Title: {result['title']}\n"
                f"Source: {result['source']}\n"
            )

            if matched_skills_str:
                formatted_result += f"✓ Matched Skills: {matched_skills_str}\n"
            if missing_skills_str:
                formatted_result += f"✗ Missing Skills: {missing_skills_str}\n"

            formatted_result += f"Content Sample: {result['content'][:200]}..."
            formatted.append(formatted_result)

        return formatted
