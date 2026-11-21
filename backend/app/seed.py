from sqlalchemy.orm import Session
from .models import Job
from .services.skills import extract_skills
from .services.recommender import ensure_job_embedding

SAMPLE_JOBS = [
("AI Backend Engineer", "Northstar AI", "Bengaluru", "Hybrid", "0-2 years",
 "Build Python backend services for LLM applications. Develop REST APIs, retrieval pipelines, embeddings, semantic search, and integrations with vector databases. Work with FastAPI, SQL, Docker, and evaluation.",
 ["python","fastapi","rest api","sql","llm","embeddings","semantic search","docker"]),
("Junior Machine Learning Engineer", "DataSpring", "Remote, India", "Remote", "0-2 years",
 "Train and evaluate machine learning models, clean datasets, build NLP pipelines, and deploy inference APIs. Work with Python, pandas, numpy, scikit-learn, TensorFlow, and model evaluation.",
 ["python","machine learning","pandas","numpy","scikit-learn","tensorflow","nlp"]),
("Full Stack Software Engineer", "Orbit Apps", "Gurugram", "On-site", "0-2 years",
 "Develop web applications using React and Node.js. Build REST APIs, work with MongoDB and PostgreSQL, write tests, and deploy reliable services. Strong JavaScript and SQL fundamentals are useful.",
 ["javascript","react","node.js","express","mongodb","postgresql","rest api","sql"]),
("RAG / AI Engineer Intern", "QueryWorks", "Bengaluru", "Hybrid", "Internship",
 "Create retrieval augmented generation systems. Chunk documents, generate embeddings, retrieve relevant passages with FAISS, integrate LLMs, build tool calling workflows, and evaluate retrieval quality.",
 ["python","rag","llm","langchain","langgraph","embeddings","faiss"]),
("Data Analyst", "MetricLoop", "Pune", "Hybrid", "0-1 years",
 "Analyze business datasets using SQL and Python. Build dashboards, perform exploratory data analysis, communicate insights, and work with pandas, numpy, Power BI, and Tableau.",
 ["sql","python","pandas","numpy","data analysis","power bi","tableau"]),
("Platform Engineer", "CloudRail", "Remote, India", "Remote", "1-3 years",
 "Build and maintain cloud-native services. Use Docker, Kubernetes, Linux, AWS, CI/CD, Python, monitoring, and SQL. Improve reliability, scalability, and deployment automation.",
 ["python","docker","kubernetes","linux","aws","sql"])
]

def seed_jobs(db: Session):
    if db.query(Job).count():
        return
    for title, company, location, mode, exp, desc, skills in SAMPLE_JOBS:
        job = Job(title=title, company=company, location=location, work_mode=mode,
                  experience=exp, description=desc, skills_csv=",".join(skills))
        db.add(job)
    db.commit()
    for job in db.query(Job).all():
        ensure_job_embedding(job)
    db.commit()
