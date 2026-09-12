"""
============================================================
  routes/interview.py  —  Interview Questions API Endpoint
============================================================
"""

from fastapi import APIRouter, UploadFile, File, Form
from agents.parser_agent import extract_text_from_file
from agents.interview_agent import run_interview_agent

router = APIRouter()


@router.post("/interview-questions")
async def generate_interview_questions(
    file: UploadFile = File(...),
    job_title: str = Form(...)
):
    """
    Generates tailored interview questions.

    Accepts:
        - file      : Resume file (PDF/DOCX)
        - job_title : Target role for question context

    Returns: JSON with technical, behavioral, and situational questions
    """

    file_bytes = await file.read()
    resume_text = extract_text_from_file(file_bytes, file.filename)

    result = run_interview_agent(resume_text, job_title)

    return {
        "success": True,
        "data": result
    }
