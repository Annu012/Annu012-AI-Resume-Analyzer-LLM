"""
PDF resume parsing — extracts raw text from an uploaded PDF.
Uses pypdf (pure-python, no system dependencies).
"""
import io
from pypdf import PdfReader


def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extracts and concatenates text from every page of a PDF."""
    reader = PdfReader(io.BytesIO(file_bytes))
    text_chunks = []
    for page in reader.pages:
        page_text = page.extract_text() or ""
        text_chunks.append(page_text)
    return "\n".join(text_chunks).strip()


def guess_candidate_name(resume_text: str) -> str:
    """
    Naive heuristic: the candidate's name is usually the first non-empty
    line of the resume that isn't an email/phone/address line.
    Good enough for a demo; swap for an NER model or LLM call in production.
    """
    for line in resume_text.splitlines():
        line = line.strip()
        if not line:
            continue
        if "@" in line or any(ch.isdigit() for ch in line):
            continue
        if len(line.split()) <= 5:
            return line
    return "Unknown Candidate"
