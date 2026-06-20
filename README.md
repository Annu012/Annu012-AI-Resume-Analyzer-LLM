# 🧠 AI Resume Analyzer — LLM-Powered Resume Screening Platform

A full-stack Generative AI application that evaluates resumes against job
descriptions to produce job-fit scores, skill-gap analysis, resume ranking,
and recruiter insights using an LLM + lightweight RAG pipeline.

Backend: **FastAPI + SQLAlchemy + JWT**. Frontend: **React (Vite)**.
LLM layer is **pluggable** — runs out of the box with a deterministic mock
scorer (no API key needed), and swaps to real OpenAI calls with one env var.

---

## 🚀 Key features

- 🔐 JWT-based recruiter authentication (register/login)
- 📄 PDF resume parsing (pypdf)
- 🧠 RAG-style grounding — TF-IDF retrieval pulls the JD chunks most
  relevant to each resume before scoring
- 🤖 Pluggable LLM evaluation layer (`mock` provider by default, `openai`
  provider when you add an API key)
- 📊 Job-fit scoring, skill match/gap analysis, improvement suggestions
- 🗄️ Persistent storage (SQLite by default, swappable to Postgres/MySQL)
- 📈 Recruiter dashboard — ranked, expandable candidate list with a radial
  score gauge

---

## 🏗️ System architecture

```
Recruiter (Browser)
        ↓
React Frontend (Dashboard)
        ↓ JWT
FastAPI Backend
        ↓
PDF Parser → RAG Retriever (TF-IDF) → LLM Provider (mock | openai)
        ↓
Database (SQLite/Postgres) — results & rankings
        ↓
Dashboard API
```

---

## 📂 Project structure

```
ai-resume-analyzer-llm/
│
├── app/
│   ├── main.py              # FastAPI entry point & routes
│   ├── config.py            # Environment config
│   ├── database.py          # DB engine/session
│   ├── models.py            # SQLAlchemy models (Recruiter, ResumeAnalysis)
│   ├── schemas.py           # Pydantic request/response models
│   ├── auth.py              # JWT + bcrypt password hashing
│   ├── dependencies.py      # Auth route guard
│   └── services/
│       ├── pdf_parser.py    # PDF text extraction
│       ├── rag_service.py   # TF-IDF retrieval / JD grounding
│       └── llm_service.py   # Pluggable LLM layer (mock / openai)
│
├── frontend/                # React (Vite) app
│   └── src/
│       ├── api/client.js        # Axios client + API calls
│       ├── context/AuthContext.jsx
│       ├── components/ScoreGauge.jsx, ProtectedRoute.jsx
│       └── pages/AuthPage.jsx, DashboardPage.jsx
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## 🔑 API endpoints

| Method | Endpoint       | Description                          |
|--------|----------------|---------------------------------------|
| POST   | `/register`    | Recruiter registration                |
| POST   | `/login`       | JWT login                             |
| POST   | `/analyze-pdf` | Upload & analyze a resume (auth req.) |
| GET    | `/dashboard`   | Ranked candidates (auth req.)         |
| GET    | `/health`      | Service health check                  |

---

## ⚙️ Setup & run locally

### 1. Backend

```bash
cd ai-resume-analyzer-llm
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs

By default `LLM_PROVIDER=mock` in `.env`, so everything works with **zero
API keys** — the mock provider scores resumes by comparing the skills
mentioned in the job description against the skills found in the resume
text.

To use real OpenAI scoring instead, edit `.env`:

```
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
```

### 2. Frontend

```bash
cd frontend
npm install
cp .env.example .env   # points VITE_API_BASE_URL at the backend
npm run dev
```

App: http://localhost:5173

---

## 🧠 How resume analysis works

1. Recruiter uploads a resume PDF + pastes a job description
2. PDF text is extracted (`pypdf`)
3. The job description is chunked and embedded with TF-IDF
4. The chunks most relevant to the resume are retrieved (RAG step)
5. The LLM provider (mock or OpenAI) evaluates the resume against that
   grounded context using a structured JSON prompt
6. Results are scored, stored, and ranked on the dashboard

## 🧪 Sample output (LLM response shape)

```json
{
  "job_fit_score": 82,
  "matched_skills": ["Python", "FastAPI", "SQL"],
  "missing_skills": ["Docker", "AWS"],
  "improvement_suggestions": [
    "Add cloud deployment experience",
    "Include system design projects"
  ]
}
```

---

## ☁️ Deployment notes

- **Backend**: AWS EC2 (Uvicorn behind Gunicorn), or any container host.
  Swap `DATABASE_URL` in `.env` to Postgres for production.
- **Frontend**: `npm run build` → static `dist/` → S3 + CloudFront, or any
  static host. Set `VITE_API_BASE_URL` to your deployed backend URL at
  build time.
- **Secrets**: environment variables only — never commit `.env`.

---

## 📌 Future improvements

- Multi-tenant company support
- Resume-to-resume comparison
- Interview question generation
- Analytics charts
- Docker + CI/CD
- Swap TF-IDF retriever for FAISS + real embeddings for larger JD corpora
