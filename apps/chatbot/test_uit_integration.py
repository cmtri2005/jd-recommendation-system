"""
Test script to verify UIT courses service integration.

This script tests:
1. UIT courses service initialization and dataset ingestion
2. Semantic search for skills
3. Integration with evaluation agent
"""

import sys
import os

# Add parent directory to path to import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from services.uit_courses_service import get_uit_courses_service
from services.learning_resources_service import get_learning_resources_service
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def test_uit_service():
    """Test UIT courses service."""
    logger.info("=" * 80)
    logger.info("Testing UIT Courses Service")
    logger.info("=" * 80)

    # Initialize service
    uit_service = get_uit_courses_service()

    # Get stats
    stats = uit_service.get_stats()
    logger.info(f"\n📊 UIT Service Stats: {stats}")

    # Test skills
    test_skills = [
        "Machine Learning",
        "Python Programming",
        "Web Development",
        "Data Analysis",
        "Deep Learning",
    ]

    for skill in test_skills:
        logger.info(f"\n🔍 Searching UIT courses for: '{skill}'")
        courses = uit_service.get_courses_for_skill(skill, max_results=3)

        if courses:
            logger.info(f"✅ Found {len(courses)} UIT courses:")
            for i, course in enumerate(courses, 1):
                logger.info(f"  {i}. {course['course_name']}")
                logger.info(f"     Khoa: {course['department']}")
                logger.info(f"     Ngành: {course['major']}")
                logger.info(f"     Skills: {course['skills'][:100]}...")
                logger.info(f"     Relevance: {course['relevance_score']:.3f}")
        else:
            logger.info(f"❌ No UIT courses found for '{skill}'")

    return uit_service


def test_online_service():
    """Test online learning resources service."""
    logger.info("\n" + "=" * 80)
    logger.info("Testing Online Learning Resources Service")
    logger.info("=" * 80)

    # Initialize service
    online_service = get_learning_resources_service()

    # Get stats
    stats = online_service.get_stats()
    logger.info(f"\n📊 Online Service Stats: {stats}")

    # Test same skills
    test_skills = ["Machine Learning", "Python Programming"]

    for skill in test_skills:
        logger.info(f"\n🔍 Searching online courses for: '{skill}'")
        courses = online_service.get_resources_for_skill(
            skill, max_results=2, min_rating=4.0
        )

        if courses:
            logger.info(f"✅ Found {len(courses)} online courses:")
            for i, course in enumerate(courses, 1):
                logger.info(f"  {i}. {course['title']}")
                logger.info(f"     Organization: {course['organization']}")
                logger.info(f"     Rating: {course['rating']}")
                logger.info(f"     URL: {course['url'][:60]}...")
        else:
            logger.info(f"❌ No online courses found for '{skill}'")

    return online_service


def test_combined_recommendations():
    """Test combined recommendations (simulating evaluation agent behavior)."""
    logger.info("\n" + "=" * 80)
    logger.info("Testing Combined Recommendations (Online + UIT)")
    logger.info("=" * 80)

    uit_service = get_uit_courses_service()
    online_service = get_learning_resources_service()

    test_skills = ["Python Programming", "Machine Learning", "Web Development"]

    for skill in test_skills:
        logger.info(f"\n🎯 Combined recommendations for: '{skill}'")

        # Get online courses
        online_courses = online_service.get_resources_for_skill(
            skill, max_results=2, min_rating=4.0
        )

        # Get UIT courses
        uit_courses = uit_service.get_courses_for_skill(skill, max_results=2)

        # Combine and format
        all_resources = []

        if online_courses:
            for r in online_courses:
                all_resources.append(
                    f"[Online] {r['title']} - {r['organization']} ({r['url'][:50]}...)"
                )

        if uit_courses:
            for r in uit_courses:
                all_resources.append(
                    f"[UIT] {r['course_name']} - {r['department']} (Ngành: {r['major']})"
                )

        if all_resources:
            logger.info(f"✅ Total: {len(all_resources)} recommendations")
            for i, resource in enumerate(all_resources, 1):
                logger.info(f"  {i}. {resource}")
        else:
            logger.info(f"❌ No recommendations found")


if __name__ == "__main__":
    try:
        logger.info("Starting UIT Courses Integration Test\n")

        # Test individual services
        test_uit_service()
        test_online_service()

        # Test combined recommendations
        test_combined_recommendations()

        logger.info("\n" + "=" * 80)
        logger.info("✅ All tests completed successfully!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"\n❌ Test failed with error: {e}", exc_info=True)
        sys.exit(1)
