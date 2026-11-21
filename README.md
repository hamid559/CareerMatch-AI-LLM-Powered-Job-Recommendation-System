# AI Job Recommendation System

An end-to-end portfolio MVP that matches a candidate's resume/profile to job descriptions using semantic embeddings, skill overlap, and a hybrid ranking score.

## Features
- Upload a PDF/DOCX/TXT resume or enter profile text.
- Extract resume text and identify skills.
- Store jobs and candidate profiles in SQLite through SQLAlchemy.
- Generate semantic embeddings with Sentence Transformers (`all-MiniLM-L6-v2`).
- Rank jobs using a hybrid score: 70% semantic similarity + 30% skill overlap.
- Explain recommendations with evidence-based reasons; optional Gemini-generated explanation.
- React + Vite frontend and FastAPI backend.
- Seed dataset of sample jobs.

> This is a portfolio MVP, not a production hiring system. The sample job data is synthetic. Do not use it to make consequential hiring decisions.

## Architecture

```text
React UI
  |-- upload resume / edit profile
  |-- browse and filter recommendations
  v
FastAPI REST API
  |-- resume parser + skill extraction
  |-- recommendation/ranking service
  |-- optional LLM explanation
  v
SQLite + SQLAlchemy
  |-- candidate profiles
  |-- job descriptions
  |-- recommendation records
  v
Sentence Transformers embeddings
  |-- semantic similarity between candidate and jobs
```

## Requirements
- Python 3.10+
- Node.js 18+
- Internet access on first backend run to download the embedding model.

## Run locally

### 1. Backend

```bash
cd backend
python -m venv .venv
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

pip install -r requirements.txt
uvicorn app.main:app --reload
```

Backend: http://localhost:8000  
Swagger API docs: http://localhost:8000/docs

On first run, the app creates `jobmatch.db` and seeds sample jobs.

### 2. Frontend

Open a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal (usually http://localhost:5173).

## Optional Gemini explanations

Copy `backend/.env.example` to `backend/.env` and set `GEMINI_API_KEY`. The app still works without it: it uses deterministic explanations based on matched skills and score components.

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/health` | Health check |
| GET | `/api/jobs` | List jobs |
| POST | `/api/jobs` | Add a job |
| POST | `/api/resume/upload` | Upload PDF/DOCX/TXT resume |
| POST | `/api/profile` | Save candidate profile text |
| GET | `/api/recommendations/{candidate_id}` | Get ranked job matches |
| GET | `/api/candidates/{candidate_id}` | Get candidate profile |

## Ranking approach

For candidate text `C` and job text `J`:

1. Encode both using the same Sentence Transformer model.
2. Compute cosine similarity `S` between their embeddings.
3. Compute skill overlap `K = |candidate skills ∩ job skills| / |job skills|`.
4. Hybrid score:

`score = 0.70 * S_normalized + 0.30 * K`

The semantic component is normalized from cosine similarity `[-1, 1]` to `[0, 1]`. This is a transparent baseline; tune the weights using a labelled validation set rather than assuming they are optimal.

## Project structure

```text
backend/
  app/
    main.py
    database.py
    models.py
    schemas.py
    services/
      parser.py
      skills.py
      embeddings.py
      recommender.py
      llm.py
    seed.py
  requirements.txt
  .env.example
frontend/
  index.html
  package.json
  vite.config.js
  src/
    main.jsx
    App.jsx
    styles.css
```

## Suggested next improvements
- Replace SQLite with PostgreSQL and add Alembic migrations.
- Add authentication, authorization, rate limits, file size limits, malware scanning, and secure object storage.
- Use a proper job ingestion pipeline and deduplication.
- Evaluate ranking with Precision@K, Recall@K, MRR, and NDCG on human-labelled query/job pairs.
- Add filters for location, work mode, experience, and salary.
- Add background jobs for embedding large job collections.
- Add privacy controls and deletion/export for candidate data.
