"""
FastAPI entry point — wires together auth, PDF parsing, RAG grounding,
the pluggable LLM layer, and persistent storage.

Run with:  uvicorn app.main:app --reload
Docs at:   http://localhost:8000/docs
"""
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.config import settings
from app.database import Base, engine, get_db
from app.models import Recruiter, ResumeAnalysis
from app.schemas import RecruiterCreate, RecruiterOut, LoginRequest, TokenResponse, AnalysisResult
from app.auth import hash_password, verify_password, create_access_token
from app.dependencies import get_current_recruiter
from app.services.pdf_parser import extract_text_from_pdf, guess_candidate_name
from app.services.rag_service import build_grounded_context
from app.services.llm_service import get_llm_provider

# Creates tables on startup if they don't exist (fine for SQLite/dev;
# use Alembic migrations for production schema changes).
Base.metadata.create_all(bind=engine)

app = FastAPI(title=settings.APP_NAME)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_ORIGIN, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health_check():
    return {"status": "ok", "llm_provider": settings.LLM_PROVIDER}


# ----------------------------------------------------------------------------
# Auth
# ----------------------------------------------------------------------------
@app.post("/register", response_model=RecruiterOut, status_code=status.HTTP_201_CREATED)
def register(payload: RecruiterCreate, db: Session = Depends(get_db)):
    existing = db.query(Recruiter).filter(Recruiter.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    recruiter = Recruiter(
        email=payload.email,
        hashed_password=hash_password(payload.password),
        company_name=payload.company_name,
    )
    db.add(recruiter)
    db.commit()
    db.refresh(recruiter)
    return recruiter


@app.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    recruiter = db.query(Recruiter).filter(Recruiter.email == payload.email).first()
    if not recruiter or not verify_password(payload.password, recruiter.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(subject=recruiter.email)
    return TokenResponse(access_token=token)


# ----------------------------------------------------------------------------
# Resume analysis
# ----------------------------------------------------------------------------
@app.post("/analyze-pdf", response_model=AnalysisResult)
async def analyze_pdf(
    job_description: str = Form(...),
    job_title: str = Form(""),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    recruiter: Recruiter = Depends(get_current_recruiter),
):
    if file.content_type != "application/pdf" and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    file_bytes = await file.read()
    resume_text = extract_text_from_pdf(file_bytes)
    if not resume_text:
        raise HTTPException(status_code=422, detail="Could not extract text from this PDF")

    candidate_name = guess_candidate_name(resume_text)

    # RAG step: ground the evaluation in the most relevant JD chunks
    grounded_context = build_grounded_context(job_description, resume_text)

    # LLM step (mock or real, decided by LLM_PROVIDER in .env)
    provider = get_llm_provider()
    result = provider.evaluate_resume(grounded_context, resume_text)

    analysis = ResumeAnalysis(
        recruiter_id=recruiter.id,
        candidate_name=candidate_name,
        filename=file.filename,
        job_title=job_title or None,
        job_fit_score=result["job_fit_score"],
        raw_resume_text=resume_text,
        job_description=job_description,
    )
    analysis.set_list_fields(
        matched=result.get("matched_skills", []),
        missing=result.get("missing_skills", []),
        suggestions=result.get("improvement_suggestions", []),
    )

    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    return analysis.to_dict()


@app.get("/dashboard", response_model=list[AnalysisResult])
def dashboard(
    db: Session = Depends(get_db),
    recruiter: Recruiter = Depends(get_current_recruiter),
):
    """Returns this recruiter's analyzed resumes, ranked by job_fit_score desc."""
    analyses = (
        db.query(ResumeAnalysis)
        .filter(ResumeAnalysis.recruiter_id == recruiter.id)
        .order_by(desc(ResumeAnalysis.job_fit_score))
        .all()
    )
    return [a.to_dict() for a in analyses]
