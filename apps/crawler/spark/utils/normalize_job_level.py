"""
Job Level Normalization Logic for TopCV Data

This module provides intelligent normalization of job level fields.
Uses pattern matching with fallback to title/experience analysis.
"""

from pyspark.sql.functions import udf, col, when, lower, regexp_extract
from pyspark.sql.types import StringType


def normalize_job_level_logic(job_level, job_title, experience_years=None):
    """
    Normalize job level to standard categories.

    Strategy:
    1. Pattern matching on common Vietnamese/English terms
    2. Fallback to job title keywords
    3. Fallback to experience years
    4. Last resort: "Not Specified"

    Args:
        job_level: Raw job level string from TopCV
        job_title: Job title for keyword analysis
        experience_years: Years of experience (if available)

    Returns:
        Normalized level: Fresher, Junior, Middle, Senior, or Not Specified
    """

    if not job_level or job_level.strip() == "":
        job_level = "unknown"

    job_level_lower = job_level.lower()
    title_lower = (job_title or "").lower()

    # === PATTERN MATCHING ON JOB LEVEL ===

    # Fresher / Intern patterns
    if any(
        keyword in job_level_lower
        for keyword in ["fresher", "intern", "thực tập", "mới", "graduate", "entry"]
    ):
        return "Fresher"

    # Junior patterns
    if any(
        keyword in job_level_lower
        for keyword in ["junior", "jr", "nhân viên", "staff", "associate"]
    ):
        return "Junior"

    # Middle patterns
    if any(
        keyword in job_level_lower
        for keyword in ["middle", "mid", "senior staff", "trung cấp", "experienced"]
    ):
        return "Middle"

    # Senior patterns
    if any(
        keyword in job_level_lower
        for keyword in ["senior", "sr", "expert", "principal", "chuyên viên", "cao cấp"]
    ):
        return "Senior"

    # Lead / Manager patterns
    if any(
        keyword in job_level_lower
        for keyword in [
            "lead",
            "leader",
            "tech lead",
            "team lead",
            "trưởng",
            "quản lý",
            "manager",
            "head",
            "chief",
            "director",
            "vp",
            "cto",
        ]
    ):
        return "Leader"

    # === FALLBACK: ANALYZE JOB TITLE ===

    # Check title for level keywords
    if any(keyword in title_lower for keyword in ["intern", "fresher", "thực tập"]):
        return "Fresher"

    if any(keyword in title_lower for keyword in ["junior", "jr"]):
        return "Junior"

    if any(keyword in title_lower for keyword in ["senior", "sr", "principal"]):
        return "Senior"

    if any(
        keyword in title_lower
        for keyword in ["lead", "leader", "manager", "head", "director"]
    ):
        return "Leader"

    # === FALLBACK: EXPERIENCE YEARS ===

    if experience_years is not None:
        if experience_years < 1:
            return "Fresher"
        elif experience_years < 2:
            return "Junior"
        elif experience_years < 5:
            return "Middle"
        elif experience_years < 8:
            return "Senior"
        else:
            return "Leader"

    # === LAST RESORT ===
    return "Not Specified"


# Spark UDF wrapper
@udf(returnType=StringType())
def normalize_job_level_udf(job_level, job_title):
    """Spark UDF for job level normalization."""
    return normalize_job_level_logic(job_level, job_title)


# === SPARK SQL APPROACH (Alternative) ===


def normalize_job_level_sql():
    """
    Returns a Spark SQL CASE WHEN expression for job level normalization.
    Use this approach if you prefer SQL-based logic.
    """
    return (
        when(
            lower(coalesce(col("job_level"), lit(""))).rlike(
                "fresher|intern|thực tập|mới|graduate|entry"
            ),
            "Fresher",
        )
        .when(
            lower(coalesce(col("job_level"), lit(""))).rlike(
                "junior|jr|nhân viên|staff|associate|developer|lập trình viên"
            ),
            "Junior",
        )
        .when(
            lower(coalesce(col("job_level"), lit(""))).rlike(
                "middle|mid|senior staff|trung cấp|experienced"
            ),
            "Middle",
        )
        .when(
            lower(coalesce(col("job_level"), lit(""))).rlike(
                "senior|sr|expert|principal|chuyên viên|cao cấp"
            ),
            "Senior",
        )
        .when(
            lower(coalesce(col("job_level"), lit(""))).rlike(
                "lead|leader|tech lead|team lead|trưởng|quản lý|manager|head|chief|director|vp|cto|phó phòng"
            ),
            "Leader",
        )
        # Fallback to job title analysis
        .when(
            lower(coalesce(col("job_title"), lit(""))).rlike("intern|fresher|thực tập"),
            "Fresher",
        )
        .when(
            lower(coalesce(col("job_title"), lit(""))).rlike(
                "junior|jr|nhân viên|developer|lập trình viên"
            ),
            "Junior",
        )
        .when(
            lower(coalesce(col("job_title"), lit(""))).rlike("middle|mid|trung cấp"),
            "Middle",
        )
        .when(
            lower(coalesce(col("job_title"), lit(""))).rlike(
                "senior|sr|principal|chuyên viên cao cấp"
            ),
            "Senior",
        )
        .when(
            lower(coalesce(col("job_title"), lit(""))).rlike(
                "lead|leader|manager|head|director|trưởng|quản lý|phó phòng"
            ),
            "Leader",
        )
        .otherwise("Not Specified")
    )


"""
USAGE IN batch_consumer.py:

# Option 1: Using UDF
from utils.normalize_job_level import normalize_job_level_udf

df_topcv_unified = df_topcv_parsed.select(
    ...
    normalize_job_level_udf(col("job_level"), col("job_title")).alias("job_level"),
    ...
)

# Option 2: Using SQL expression (preferred - faster)
from utils.normalize_job_level import normalize_job_level_sql

df_topcv_unified = df_topcv_parsed.select(
    ...
    normalize_job_level_sql().alias("job_level"),
    ...
)
"""
