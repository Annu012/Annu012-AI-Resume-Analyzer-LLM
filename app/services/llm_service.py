"""
Pluggable LLM layer.

LLM_PROVIDER=mock    -> deterministic, offline, keyword-overlap scoring (default).
                         Lets the whole app run end-to-end with zero API keys.
LLM_PROVIDER=openai  -> real call to OpenAI's chat completions API using a
                         structured JSON-output prompt. Requires OPENAI_API_KEY.

Both providers return the exact same shape, so the rest of the app (routes,
DB, frontend) never needs to know which one is active.
"""
import json
import re
from abc import ABC, abstractmethod
from typing import Dict, List

from app.config import settings

RESUME_EVAL_SYSTEM_PROMPT = """You are an expert technical recruiter and resume screener.
Given a JOB DESCRIPTION (grounded context) and a RESUME, evaluate how well the
candidate fits the role.

Respond ONLY with valid JSON, no markdown fences, no preamble, in exactly this shape:
{
  "job_fit_score": <integer 0-100>,
  "matched_skills": [<strings>],
  "missing_skills": [<strings>],
  "improvement_suggestions": [<strings>]
}
"""


class BaseLLMProvider(ABC):
    @abstractmethod
    def evaluate_resume(self, job_description_context: str, resume_text: str) -> Dict:
        ...


# ----------------------------------------------------------------------------
# Mock provider: deterministic skill-overlap heuristic. No network calls.
# ----------------------------------------------------------------------------
COMMON_SKILLS = [
    "python", "java", "javascript", "typescript", "react", "node", "fastapi",
    "django", "flask", "sql", "postgresql", "mysql", "mongodb", "docker",
    "kubernetes", "aws", "azure", "gcp", "git", "ci/cd", "rest api",
    "graphql", "machine learning", "deep learning", "nlp", "pandas",
    "numpy", "tensorflow", "pytorch", "langchain", "llm", "rag",
    "microservices", "system design", "agile", "scrum",
]


class MockLLMProvider(BaseLLMProvider):
    def evaluate_resume(self, job_description_context: str, resume_text: str) -> Dict:
        jd_lower = job_description_context.lower()
        resume_lower = resume_text.lower()

        jd_skills = {s for s in COMMON_SKILLS if s in jd_lower}
        if not jd_skills:
            # fall back to naive keyword extraction from JD if no known skills found
            jd_skills = set(list(dict.fromkeys(re.findall(r"[a-zA-Z+#.]{3,}", jd_lower)))[:15])

        matched = sorted(s for s in jd_skills if s in resume_lower)
        missing = sorted(s for s in jd_skills if s not in resume_lower)

        total = len(jd_skills) or 1
        score = round((len(matched) / total) * 100)
        # small floor/ceiling so scores feel realistic, not 0/100 extremes
        score = max(15, min(score, 97))

        suggestions = []
        for skill in missing[:3]:
            suggestions.append(f"Consider adding measurable experience with {skill}.")
        if not suggestions:
            suggestions.append("Strong alignment — consider quantifying impact with metrics.")

        return {
            "job_fit_score": score,
            "matched_skills": [s.title() for s in matched] or ["General Experience"],
            "missing_skills": [s.title() for s in missing],
            "improvement_suggestions": suggestions,
        }


# ----------------------------------------------------------------------------
# OpenAI provider: real LLM call. Activate by setting LLM_PROVIDER=openai
# and OPENAI_API_KEY in .env. Requires `pip install openai`.
# ----------------------------------------------------------------------------
class OpenAILLMProvider(BaseLLMProvider):
    def __init__(self):
        from openai import OpenAI  # imported lazily so mock mode has no hard dependency
        if not settings.OPENAI_API_KEY:
            raise RuntimeError("OPENAI_API_KEY is not set but LLM_PROVIDER=openai")
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = settings.OPENAI_MODEL

    def evaluate_resume(self, job_description_context: str, resume_text: str) -> Dict:
        user_prompt = f"""JOB DESCRIPTION (relevant context):
{job_description_context}

RESUME:
{resume_text}
"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": RESUME_EVAL_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.2,
        )
        content = response.choices[0].message.content.strip()
        content = re.sub(r"^```json|```$", "", content, flags=re.MULTILINE).strip()
        return json.loads(content)


def get_llm_provider() -> BaseLLMProvider:
    if settings.LLM_PROVIDER == "openai":
        return OpenAILLMProvider()
    return MockLLMProvider()
