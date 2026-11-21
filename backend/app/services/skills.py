
import re
import hashlib
from collections import OrderedDict

from .llm import (
    extract_skills_with_llm,
    extract_skills_batch_with_llm
)

# Cache successful Gemini skill extraction results
SKILL_CACHE = OrderedDict()
MAX_CACHE_SIZE = 500


SKILL_VOCAB = [
    # Programming languages
    "python", "java", "c++", "javascript", "typescript",

    # Databases
    "sql", "postgresql", "mysql", "mongodb", "redis",

    # Data analysis
    "excel", "advanced excel", "power bi", "tableau",
    "data analysis", "data visualization", "statistics",
    "business analysis", "data cleaning", "data modeling",

    # Python libraries
    "pandas", "numpy", "scikit-learn",

    # AI and machine learning
    "machine learning", "deep learning", "nlp",
    "tensorflow", "pytorch", "llm", "generative ai",
    "langchain", "langgraph", "rag", "embeddings",

    # Web development
    "html", "css", "react", "node.js", "express",
    "fastapi", "flask", "django", "rest api",

    # Cloud and DevOps
    "aws", "azure", "gcp", "docker", "kubernetes",
    "git", "linux", "kafka",

    # Computer science
    "data structures", "algorithms", "system design",
    "faiss", "vector database", "semantic search"
]



def extract_skills(text: str, source_type: str = "resume") -> list[str]:

    if not text or not text.strip():
        return []

    # Create a unique cache key for this text
    cache_key = (
        source_type,
        hashlib.sha256(text.encode("utf-8")).hexdigest()
    )

    # Reuse previously extracted skills if available
    if cache_key in SKILL_CACHE:
        SKILL_CACHE.move_to_end(cache_key)
        return SKILL_CACHE[cache_key].copy()

    # Step 1: Ask Gemini to identify skills
    llm_skills = extract_skills_with_llm(
        text,
        source_type=source_type
    )

    # If Gemini successfully returns a result, cache it
    if llm_skills is not None:

        cleaned_skills = sorted(set(
            skill.strip().lower()
            for skill in llm_skills
            if isinstance(skill, str) and skill.strip()
        ))

        SKILL_CACHE[cache_key] = cleaned_skills
        SKILL_CACHE.move_to_end(cache_key)

        if len(SKILL_CACHE) > MAX_CACHE_SIZE:
            SKILL_CACHE.popitem(last=False)

        return cleaned_skills

    # Step 2: Fallback to vocabulary-based extraction
    lower = text.lower()
    found = []

    for skill in SKILL_VOCAB:
        pattern = (
            r"(?<![a-z0-9])"
            + re.escape(skill)
            + r"(?![a-z0-9])"
        )

        if re.search(pattern, lower):
            found.append(skill)

    return sorted(set(found))


def extract_skills_batch(texts: list[str]) -> list[list[str]]:

    results = [None] * len(texts)
    missing_indices = []

    # Step 1: Check cache first
    for index, text in enumerate(texts):

        if not text or not text.strip():
            results[index] = []
            continue

        cache_key = (
            "job description",
            hashlib.sha256(text.encode("utf-8")).hexdigest()
        )

        if cache_key in SKILL_CACHE:
            SKILL_CACHE.move_to_end(cache_key)
            results[index] = SKILL_CACHE[cache_key].copy()
        else:
            missing_indices.append(index)

    # Step 2: Send only uncached descriptions to Gemini
    if missing_indices:

        uncached_texts = [texts[i] for i in missing_indices]

        batch_results = extract_skills_batch_with_llm(
            uncached_texts
        )

        # Step 3: Save successful Gemini results in cache
        if batch_results is not None and len(batch_results) == len(uncached_texts):

            for index, skills in zip(missing_indices, batch_results):

                cleaned = sorted({
                    skill.strip().lower()
                    for skill in skills
                    if isinstance(skill, str) and skill.strip()
                })

                results[index] = cleaned

                cache_key = (
                    "job description",
                    hashlib.sha256(texts[index].encode("utf-8")).hexdigest()
                )

                SKILL_CACHE[cache_key] = cleaned
                SKILL_CACHE.move_to_end(cache_key)

                if len(SKILL_CACHE) > MAX_CACHE_SIZE:
                    SKILL_CACHE.popitem(last=False)

        else:
            # Step 4: Use regex directly if Gemini batch fails
            for index in missing_indices:
                lower = texts[index].lower()
                found = []

                for skill in SKILL_VOCAB:
                    pattern = (
                        r"(?<![a-z0-9])"
                        + re.escape(skill)
                        + r"(?![a-z0-9])"
                    )

                    if re.search(pattern, lower):
                        found.append(skill)

                results[index] = sorted(set(found))

    return results

