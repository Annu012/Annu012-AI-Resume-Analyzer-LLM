"""
Centralized environment configuration.
Loads values from .env (see .env.example) with sane local defaults.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # --- General ---
    APP_NAME: str = "AI Resume Analyzer"
    ENV: str = os.getenv("ENV", "development")

    # --- Database ---
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./resume_analyzer.db")

    # --- Auth / JWT ---
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-this-secret-in-production")
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))

    # --- LLM provider ---
    # "mock"   -> deterministic offline scoring, no API key needed (default)
    # "openai" -> real OpenAI call, requires OPENAI_API_KEY
    LLM_PROVIDER: str = os.getenv("LLM_PROVIDER", "mock")
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # --- CORS ---
    FRONTEND_ORIGIN: str = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")


settings = Settings()
