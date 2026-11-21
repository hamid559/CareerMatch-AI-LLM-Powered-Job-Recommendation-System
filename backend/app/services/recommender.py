
import json

from .embeddings import embed, cosine_from_normalized
from .llm import explain_match


def job_text(job):
    return (
        f"{job.title}. {job.description}. "
        f"Required skills: {job.skills_csv}. "
        f"Experience: {job.experience}. "
        f"Location: {job.location}."
    )


def ensure_job_embedding(job):
    if not job.embedding_json:
        job.embedding_json = json.dumps(embed(job_text(job)))

    return json.loads(job.embedding_json)


def recommend(candidate, jobs, top_k=10):

    candidate_skills = {
        skill.strip().lower()
        for skill in candidate.skills_csv.split(",")
        if skill.strip()
    }

    candidate_vec = embed(candidate.resume_text)

    results = []

    # Step 1: Calculate match scores for all jobs
    for job in jobs:

        
        job_skills = {
            skill.strip().lower()
            for skill in job.skills_csv.split(",")
            if skill.strip()
        }

        # Calculate semantic similarity
        semantic = cosine_from_normalized(
            candidate_vec,
            ensure_job_embedding(job)
        )

        semantic01 = max(
            0.0,
            min(1.0, (semantic + 1.0) / 2.0)
        )

        # Calculate skill overlap only if job skills are available
        if job_skills:
            overlap = (
                len(candidate_skills & job_skills)
                / len(job_skills)
            )

            skill_score = round(overlap * 100, 2)

            # Combined score: 70% semantic + 30% skill match
            score = 100 * (
                0.70 * semantic01 + 0.30 * overlap
            )

        else:
            # If no job skills are detected, use semantic score only
            skill_score = None
            score = 100 * semantic01

        matched = sorted(candidate_skills & job_skills)
        missing = sorted(job_skills - candidate_skills)


        results.append({
            "job": job,
            "score": round(score, 2),
            "semantic_score": round(semantic01 * 100, 2),
            "skill_score": skill_score,
            "matched_skills": matched,
            "missing_skills": missing,
            "explanation": ""
        })

    # Step 2: Sort jobs by match score
    results = sorted(
        results,
        key=lambda x: x["score"],
        reverse=True
    )[:top_k]

    # Step 3: Generate Gemini explanations only for top 5
    for index, item in enumerate(results):

        job = item["job"]

        if index < 3:

            item["explanation"] = explain_match(
                job.title,
                job.company,
                item["matched_skills"],
                item["missing_skills"],
                item["score"]
            )

        else:

            # Simple explanation without an API call
            if item["matched_skills"]:
                item["explanation"] = (
                    f"This job matches your profile through "
                    f"{', '.join(item['matched_skills'][:5])}. "
                    "Review the requirements before applying."
                )
            else:
                item["explanation"] = (
                    "This job has semantic similarity to your "
                    "profile, but no exact skills were matched."
                )

    return results
