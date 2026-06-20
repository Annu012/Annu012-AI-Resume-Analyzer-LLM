"""
SQLAlchemy ORM models: Recruiter (auth) and ResumeAnalysis (results/rankings).
"""
import datetime
import json

from sqlalchemy import Column, Integer, String, Float, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class Recruiter(Base):
    __tablename__ = "recruiters"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    company_name = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    analyses = relationship("ResumeAnalysis", back_populates="recruiter")


class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"

    id = Column(Integer, primary_key=True, index=True)
    recruiter_id = Column(Integer, ForeignKey("recruiters.id"), nullable=False)

    candidate_name = Column(String, nullable=True)
    filename = Column(String, nullable=False)
    job_title = Column(String, nullable=True)

    job_fit_score = Column(Float, nullable=False)
    matched_skills = Column(Text, nullable=True)        # JSON-encoded list
    missing_skills = Column(Text, nullable=True)         # JSON-encoded list
    improvement_suggestions = Column(Text, nullable=True)  # JSON-encoded list

    raw_resume_text = Column(Text, nullable=True)
    job_description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    recruiter = relationship("Recruiter", back_populates="analyses")

    # --- convenience helpers for JSON list fields ---
    def set_list_fields(self, matched, missing, suggestions):
        self.matched_skills = json.dumps(matched or [])
        self.missing_skills = json.dumps(missing or [])
        self.improvement_suggestions = json.dumps(suggestions or [])

    def to_dict(self):
        return {
            "id": self.id,
            "candidate_name": self.candidate_name,
            "filename": self.filename,
            "job_title": self.job_title,
            "job_fit_score": self.job_fit_score,
            "matched_skills": json.loads(self.matched_skills or "[]"),
            "missing_skills": json.loads(self.missing_skills or "[]"),
            "improvement_suggestions": json.loads(self.improvement_suggestions or "[]"),
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
