"""API Routes for JD Recommendation System."""

from fastapi import APIRouter, HTTPException, UploadFile, Form, File
from typing import List, Optional
import logging
import tempfile
import os
import hashlib
import time
from functools import lru_cache

from core.agents.orchestrator import Orchestrator
from services.learning_resources_service import get_learning_resources_service
from tools.document_loader import pdf_loader, docx_loader
from models.response import (
    EvaluationResponse,
    LearningResourceResponse,
    SkillGapResponse,
    ScoreBreakdownResponse,
    MatchItemResponse,
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# Simple cache for evaluation results (TTL: 1 hour)
EVAL_CACHE = {}
CACHE_TTL = 3600


def get_cache_key(resume_text: str, jd_text: str) -> str:
    """Generate cache key from resume and JD text."""
    combined = f"{resume_text[:500]}||{jd_text[:500]}"
    return hashlib.md5(combined.encode()).hexdigest()


def get_cached_result(cache_key: str):
    """Get cached result if not expired."""
    if cache_key in EVAL_CACHE:
        cached_data, timestamp = EVAL_CACHE[cache_key]
        if time.time() - timestamp < CACHE_TTL:
            logger.info(f"✅ Cache HIT for key: {cache_key[:8]}...")
            return cached_data
        else:
            # Expired, remove from cache
            del EVAL_CACHE[cache_key]
    return None


def set_cached_result(cache_key: str, result):
    """Store result in cache with timestamp."""
    EVAL_CACHE[cache_key] = (result, time.time())
    logger.info(f"💾 Cached result for key: {cache_key[:8]}...")


@router.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "jd-recommendation-api", "version": "1.0.0"}


@router.post("/api/evaluate", response_model=EvaluationResponse)
async def evaluate_resume(
    resume_file: UploadFile = File(None),
    jd_file: UploadFile = File(None),
    jd_text: Optional[str] = Form(None),
):
    """
    Evaluate resume against job description.

    Accepts file uploads and extracts text server-side.
    """
    try:
        logger.info("Starting resume evaluation...")
        logger.info(f"DEBUG - resume_file: {resume_file}")
        logger.info(f"DEBUG - jd_file: {jd_file}")
        logger.info(f"DEBUG - jd_text: {jd_text}")

        # Extract resume text from file
        if not resume_file:
            logger.error("Resume file is missing!")
            raise HTTPException(status_code=400, detail="Resume file is required")

        # Save and extract resume
        with tempfile.NamedTemporaryFile(
            delete=False, suffix=os.path.splitext(resume_file.filename)[1]
        ) as tmp:
            content = await resume_file.read()
            tmp.write(content)
            tmp_path = tmp.name

        try:
            if tmp_path.endswith(".pdf"):
                resume_text = pdf_loader(tmp_path)
            elif tmp_path.endswith((".docx", ".doc")):
                resume_text = docx_loader(tmp_path)
            else:
                raise HTTPException(
                    status_code=400, detail="Resume must be PDF or DOCX"
                )
        finally:
            os.unlink(tmp_path)

        logger.info(f"Resume extracted: {len(resume_text)} characters")

        # Extract JD text
        if jd_file:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=os.path.splitext(jd_file.filename)[1]
            ) as tmp:
                content = await jd_file.read()
                tmp.write(content)
                tmp_path = tmp.name

            try:
                if tmp_path.endswith(".pdf"):
                    jd_text = pdf_loader(tmp_path)
                elif tmp_path.endswith((".docx", ".doc")):
                    jd_text = docx_loader(tmp_path)
                elif tmp_path.endswith(".txt"):
                    with open(tmp_path, "r", encoding="utf-8") as f:
                        jd_text = f.read()
                else:
                    raise HTTPException(
                        status_code=400, detail="JD must be PDF, DOCX, or TXT"
                    )
            finally:
                os.unlink(tmp_path)

        if not jd_text:
            raise HTTPException(status_code=400, detail="JD text or file is required")

        logger.info(f"JD extracted: {len(jd_text)} characters")

        # Check cache first
        cache_key = get_cache_key(resume_text, jd_text)
        cached_result = get_cached_result(cache_key)

        if cached_result:
            return cached_result

        # Initialize orchestrator
        orchestrator = Orchestrator()
        graph = orchestrator.orchestrate()

        # Run evaluation
        result = graph.invoke(
            {
                "resume_text": resume_text,
                "jd_text": jd_text,
                "messages": [],
            }
        )

        # Extract evaluation result
        eval_result = result["messages"][-1]

        # Convert to response model
        response = EvaluationResponse(
            total_score=eval_result.total_score,
            score_breakdown=ScoreBreakdownResponse(
                hard_skills_score=eval_result.score_breakdown.hard_skills_score,
                soft_skills_score=eval_result.score_breakdown.soft_skills_score,
                work_experience_score=eval_result.score_breakdown.work_experience_score,
                years_of_experience_score=eval_result.score_breakdown.years_of_experience_score,
                education_score=eval_result.score_breakdown.education_score,
                extras_score=eval_result.score_breakdown.extras_score,
            ),
            strengths=[
                MatchItemResponse(category=s.category, details=s.details)
                for s in eval_result.strengths
            ],
            weaknesses=[
                MatchItemResponse(category=w.category, details=w.details)
                for w in eval_result.weaknesses
            ],
            missing_hard_skills=[
                SkillGapResponse(
                    skill_name=skill.skill_name,
                    importance=skill.importance,
                    learning_resources=skill.learning_resources,
                )
                for skill in eval_result.missing_hard_skills
            ],
            summary=eval_result.summary,
            recommendation=eval_result.recommendation,
            recommendation_reason=eval_result.recommendation_reason,
            retrieved_jobs=result.get("retrieved_jobs", []),
        )

        logger.info(f"Evaluation complete: Score={eval_result.total_score}/100")

        # Cache the result
        set_cached_result(cache_key, response)

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Evaluation failed: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evaluation failed: {str(e)}")


@router.get(
    "/api/learning-resources/{skill}", response_model=List[LearningResourceResponse]
)
async def get_learning_resources(
    skill: str, max_results: int = 3, min_rating: float = 4.0
):
    """
    Get verified learning resources for a specific skill.

    Args:
        skill: Skill name to search for
        max_results: Maximum number of resources to return (default: 3)
        min_rating: Minimum course rating (default: 4.0)

    Returns:
        List of verified learning resources
    """
    try:
        logger.info(f"Fetching learning resources for skill: {skill}")

        service = get_learning_resources_service()
        resources = service.get_resources_for_skill(
            skill=skill, max_results=max_results, min_rating=min_rating
        )

        response = [
            LearningResourceResponse(
                title=r["title"],
                organization=r["organization"],
                url=r["url"],
                rating=r["rating"],
                difficulty=r["difficulty"],
                type=r["type"],
                verified=r["verified"],
            )
            for r in resources
        ]

        logger.info(f"Found {len(response)} resources for '{skill}'")
        return response

    except Exception as e:
        logger.error(f"Failed to fetch learning resources: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch resources: {str(e)}"
        )


@router.get("/api/kb-stats")
async def get_kb_stats():
    """Get knowledge base statistics."""
    try:
        service = get_learning_resources_service()
        stats = service.get_stats()
        return {
            "total_courses": stats.get("total_courses", 0),
            "collection_name": stats.get("collection_name", "unknown"),
        }
    except Exception as e:
        logger.error(f"Failed to fetch KB stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch stats: {str(e)}")
