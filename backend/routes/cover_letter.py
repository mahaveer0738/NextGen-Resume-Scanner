"""
============================================================
  routes/cover_letter.py  —  Cover Letter API Endpoint
============================================================
"""

from fastapi import APIRouter, UploadFile, File, Form
from agents.parser_agent import extract_text_from_file
from agents.cover_letter_agent import run_cover_letter_agent

router = APIRouter()


@router.post("/cover-letter")
async def generate_cover_letter(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    company_name: str = Form("")     # Optional — empty string by default
):
    """
    Generates a personalized cover letter.

    Accepts:
        - file         : Resume file (PDF/DOCX)
        - job_title    : Target job role (e.g., "Software Engineer")
        - company_name : Optional company name

    Returns: JSON with the generated cover letter text
    """

    file_bytes = await file.read()
    resume_text = extract_text_from_file(file_bytes, file.filename)

    result = run_cover_letter_agent(resume_text, job_title, company_name)

    return {
        "success": True,
        "data": result
    }
