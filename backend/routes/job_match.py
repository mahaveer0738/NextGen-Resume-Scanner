"""
============================================================
  routes/job_match.py  —  Job Match API Endpoint
============================================================
"""

from fastapi import APIRouter, UploadFile, File, Form
from agents.parser_agent import extract_text_from_file
from agents.job_match_agent import run_job_match_agent

router = APIRouter()


@router.post("/job-match")
async def job_match(
    file: UploadFile = File(...),
    job_description: str = Form(...)   # 📌 Form() = text field from a form
):
    """
    Compares resume against a job description.

    Accepts:
        - file           : Resume file (PDF/DOCX)
        - job_description: Job description text (pasted by user)

    Returns: JSON with compatibility score and matched/missing skills
    """

    file_bytes = await file.read()
    resume_text = extract_text_from_file(file_bytes, file.filename)

    result = run_job_match_agent(resume_text, job_description)

    return {
        "success": True,
        "data": result
    }
