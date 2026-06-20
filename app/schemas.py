"""
Pydantic schemas used for request validation and response shaping.
"""
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field


class RecruiterCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    company_name: Optional[str] = None


class RecruiterOut(BaseModel):
    id: int
    email: EmailStr
    company_name: Optional[str] = None

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AnalysisResult(BaseModel):
    id: int
    candidate_name: Optional[str]
    filename: str
    job_title: Optional[str]
    job_fit_score: float
    matched_skills: List[str]
    missing_skills: List[str]
    improvement_suggestions: List[str]
    created_at: Optional[str]
