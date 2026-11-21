
import os
import json
from google import genai


# Tracks whether Gemini quota has been exhausted
GEMINI_QUOTA_EXHAUSTED = False


def get_gemini_client():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None

    return genai.Client(api_key=api_key)


def is_quota_error(error: Exception) -> bool:
    error_text = str(error).lower()

    quota_indicators = [
        "quota",
        "resource_exhausted",
        "rate limit",
        "429",
        "requests per day limit exceeded"
    ]

    return any(
        indicator in error_text
        for indicator in quota_indicators
    )


def handle_gemini_error(error: Exception, operation: str):
    """
    Detect quota errors and disable further Gemini requests
    for the current backend process.
    """
    global GEMINI_QUOTA_EXHAUSTED

    if is_quota_error(error):
        GEMINI_QUOTA_EXHAUSTED = True

        print(
            "Gemini quota exhausted. "
            "Switching to local fallback mode."
        )
    else:
        print(f"Gemini {operation} failed: {error}")


def extract_skills_with_llm(
    text: str,
    source_type: str = "resume"
):
    """
    Extract skills from a resume or job description.
    Returns None if Gemini is unavailable.
    """

    if not text or not text.strip():
        return None

    if GEMINI_QUOTA_EXHAUSTED:
        return None

    try:
        client = get_gemini_client()

        if client is None:
            return None

        model_name = os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash"
        )

        prompt = f"""
You are an expert recruitment and resume analysis assistant.

Analyze this {source_type}.

Extract technical skills, programming languages,
frameworks, libraries, databases, software tools,
analytical skills and relevant professional skills.

Rules:
1. Extract only skills supported by the supplied text.
2. Never invent skills.
3. Do not infer skills just from a job title.
4. Normalize equivalent names consistently.
5. Remove duplicate skills.
6. Return an empty list if no skills are found.

For a job description, distinguish required skills
from preferred skills.

Text:
{text}
"""

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "OBJECT",
                    "properties": {
                        "skills": {
                            "type": "ARRAY",
                            "items": {"type": "STRING"}
                        }
                    },
                    "required": ["skills"]
                }
            }
        )

        data = json.loads(response.text)

        return sorted({
            skill.strip().lower()
            for skill in data.get("skills", [])
            if isinstance(skill, str) and skill.strip()
        })

    except Exception as e:
        handle_gemini_error(e, "skill extraction")
        return None


def extract_skills_batch_with_llm(
    texts: list[str]
) -> list[list[str]] | None:
    """
    Extract skills from multiple job descriptions
    using one Gemini API request.

    Results follow the same order as the input.
    """

    if not texts:
        return []

    if GEMINI_QUOTA_EXHAUSTED:
        return None

    try:
        client = get_gemini_client()

        if client is None:
            return None

        model_name = os.getenv(
            "GEMINI_MODEL",
            "gemini-2.5-flash"
        )

        jobs_text = "\n\n".join(
            f"JOB {i}:\n{text}"
            for i, text in enumerate(texts)
        )

        prompt = f"""
You are an expert recruitment assistant.

Extract technical and professional skills from each
job description separately.

Rules:
1. Extract only skills explicitly supported by the text.
2. Never invent skills.
3. Do not infer skills from job titles alone.
4. Normalize skill names consistently.
5. Remove duplicates.
6. Return an empty skills list if none are found.
7. Preserve the original job index.

Here are the job descriptions:

{jobs_text}
"""

        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config={
                "response_mime_type": "application/json",
                "response_schema": {
                    "type": "OBJECT",
                    "properties": {
                        "jobs": {
                            "type": "ARRAY",
                            "items": {
                                "type": "OBJECT",
                                "properties": {
                                    "index": {
                                        "type": "INTEGER"
                                    },
                                    "skills": {
                                        "type": "ARRAY",
                                        "items": {
                                            "type": "STRING"
                                        }
                                    }
                                },
                                "required": [
                                    "index",
                                    "skills"
                                ]
                            }
                        }
                    },
                    "required": ["jobs"]
                }
            }
        )

        data = json.loads(response.text)

        results = [[] for _ in texts]

        for item in data.get("jobs", []):
            index = item.get("index")

            if isinstance(index, int) and 0 <= index < len(texts):
                results[index] = sorted({
                    skill.strip().lower()
                    for skill in item.get("skills", [])
                    if isinstance(skill, str) and skill.strip()
                })

        return results

    except Exception as e:
        handle_gemini_error(e, "batch skill extraction")
        return None


def explain_match(
    job_title: str,
    company: str,
    matched: list[str],
    missing: list[str],
    score: float
) -> str:
    """
    Generate an AI explanation when Gemini is available.
    Otherwise, generate a local explanation.
    """

    if not GEMINI_QUOTA_EXHAUSTED:

        try:
            client = get_gemini_client()

            if client is not None:

                model_name = os.getenv(
                    "GEMINI_MODEL",
                    "gemini-2.5-flash"
                )

                prompt = f"""
Explain this job recommendation in two concise sentences.

Job: {job_title} at {company}
Matched skills: {matched}
Other listed job skills: {missing}
Match score: {score:.1f}%

Do not invent candidate experience.
Mention that this is an approximate ranking,
not a hiring decision.
"""

                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )

                if response.text:
                    return response.text.strip()

        except Exception as e:
            handle_gemini_error(e, "explanation")

    # Local fallback explanation
    if matched:
        return (
            f"Your profile overlaps with this role in "
            f"{', '.join(matched[:6])}. "
            "Review the job requirements before applying."
        )

    return (
        "Your profile has semantic similarity to this role, "
        "but no exact matching skills were detected. "
        "Review the job requirements before applying."
    )
