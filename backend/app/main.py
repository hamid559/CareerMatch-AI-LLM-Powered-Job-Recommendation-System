
from .services.adzuna import fetch_adzuna_jobs
from .services.skills import extract_skills, extract_skills_batch
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from dotenv import load_dotenv
from .database import Base, engine, get_db
from .models import Candidate, Job
from .schemas import ProfileIn, JobIn
from .services.parser import extract_resume_text
from .services.recommender import recommend, ensure_job_embedding
from .seed import seed_jobs
import os


load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    from .database import SessionLocal
    db = SessionLocal()
    try:
        seed_jobs(db)
    finally:
        db.close()
    yield

app = FastAPI(title="AI Job Recommendation API", version="1.0.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "AI Job Recommendation API"}

@app.get("/api/jobs")
def list_jobs(db: Session = Depends(get_db)):
    jobs = db.query(Job).all()
    return [{"id": j.id, "title": j.title, "company": j.company, "location": j.location,
             "work_mode": j.work_mode, "experience": j.experience,
             "description": j.description, "skills": j.skills_csv.split(",") if j.skills_csv else []}
            for j in jobs]

@app.post("/api/jobs")
def create_job(payload: JobIn, db: Session = Depends(get_db)):
    job = Job(title=payload.title, company=payload.company, location=payload.location,
              work_mode=payload.work_mode, experience=payload.experience,
              description=payload.description, skills_csv=",".join(s.lower() for s in payload.skills))
    db.add(job)
    db.commit()
    db.refresh(job)
    ensure_job_embedding(job)
    db.commit()
    return {"id": job.id, "message": "Job created"}

@app.post("/api/resume/upload")
async def upload_resume(file: UploadFile = File(...), db: Session = Depends(get_db)):
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:
        raise HTTPException(413, "Resume must be 5 MB or smaller.")
    try:
        text = extract_resume_text(file.filename or "resume.txt", content)
    except ValueError as e:
        raise HTTPException(400, str(e))
    skills = extract_skills(text)
    candidate = Candidate(name="Candidate", resume_text=text, skills_csv=",".join(skills))
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return {"candidate_id": candidate.id, "extracted_skills": skills, "resume_preview": text[:700]}

@app.post("/api/profile")
def create_profile(payload: ProfileIn, db: Session = Depends(get_db)):
    skills = extract_skills(payload.resume_text)
    candidate = Candidate(name=payload.name, resume_text=payload.resume_text, skills_csv=",".join(skills))
    db.add(candidate)
    db.commit()
    db.refresh(candidate)
    return {"candidate_id": candidate.id, "extracted_skills": skills}

@app.get("/api/candidates/{candidate_id}")
def get_candidate(candidate_id: int, db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(404, "Candidate not found")
    return {"id": candidate.id, "name": candidate.name,
            "skills": candidate.skills_csv.split(",") if candidate.skills_csv else [],
            "resume_preview": candidate.resume_text[:700]}

@app.get("/api/recommendations/{candidate_id}")
def get_recommendations(candidate_id: int, top_k: int = Query(10, ge=1, le=50),
                        db: Session = Depends(get_db)):
    candidate = db.get(Candidate, candidate_id)
    if not candidate:
        raise HTTPException(404, "Candidate not found")
    jobs = db.query(Job).all()
    ranked = recommend(candidate, jobs, top_k)
    return [{
        "job": {"id": x["job"].id, "title": x["job"].title, "company": x["job"].company,
                "location": x["job"].location, "work_mode": x["job"].work_mode,
                "experience": x["job"].experience, "description": x["job"].description,
                "skills": x["job"].skills_csv.split(",") if x["job"].skills_csv else []},
        "score": x["score"], "semantic_score": x["semantic_score"],
        "skill_score": x["skill_score"], "matched_skills": x["matched_skills"],
        "missing_skills": x["missing_skills"], "explanation": x["explanation"]
    } for x in ranked]


@app.get("/api/jobs/live/{candidate_id}")
def get_live_recommendations(
    candidate_id: int,
    query: str = "Data Analyst",
    location: str = "India",
    top_k: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    candidate = db.get(Candidate, candidate_id)

    if not candidate:
        raise HTTPException(404, "Candidate not found")

    try:
        live_jobs = fetch_adzuna_jobs(
            query=query,
            location=location,
            results_per_page=20
        )
    except (ValueError, RuntimeError) as e:
        raise HTTPException(502, str(e))

    jobs = []

    # Prepare all job descriptions and extract skills in one batch request.
    job_texts = [
        item.get("title", "") + " " + item.get("description", "")
        for item in live_jobs
    ]
    batch_skills = extract_skills_batch(job_texts)

    # Create transient Job objects using the extracted skills.
    for item, skills in zip(live_jobs, batch_skills):
        description = item.get("description", "")

        job = Job(
            title=item.get("title", "Unknown"),
            company=item.get("company", {}).get("display_name", "Unknown"),
            location=item.get("location", {}).get("display_name", location),
            work_mode="Not specified",
            experience="Not specified",
            description=description,
            skills_csv=",".join(skills),
            embedding_json=""
        )

        job.redirect_url = item.get("redirect_url", "")
        job.salary_min = item.get("salary_min")
        job.salary_max = item.get("salary_max")

        jobs.append(job)

    ranked = recommend(candidate, jobs, top_k)

    return {
        "source": "Adzuna Live Jobs",
        "total_jobs_fetched": len(jobs),
        "results": [
            {
                "title": x["job"].title,
                "company": x["job"].company,
                "location": x["job"].location,
                "description": x["job"].description,
                "skills": x["job"].skills_csv.split(",")
                    if x["job"].skills_csv else [],
                "score": x["score"],
                "semantic_score": x["semantic_score"],
                "skill_score": x["skill_score"],
                "matched_skills": x["matched_skills"],
                "missing_skills": x["missing_skills"],
                "explanation": x["explanation"],
                "apply_url": x["job"].redirect_url,
                "salary_min": x["job"].salary_min,
                "salary_max": x["job"].salary_max
            }
            for x in ranked
        ]
    }

