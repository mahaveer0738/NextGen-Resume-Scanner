"""
============================================================
  routes/interview.py  —  Interview Questions API Endpoint
============================================================
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, UploadFile, File, Form, Depends
import json

from agents.parser_agent import extract_text_from_file
from agents.interview_agent import run_interview_agent
from database import get_db
import models
from utils.auth_utils import get_optional_user

router = APIRouter()


@router.post("/interview-questions")
async def generate_interview_questions(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    current_user: Optional[models.User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
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

    # Save to history if logged in
    if current_user:
        try:
            history_record = models.ScanHistory(
                user_id=current_user.id,
                filename=file.filename,
                scan_type="interview",
                detected_role=job_title,
                full_result=json.dumps(result)
            )
            db.add(history_record)
            db.commit()
        except Exception:
            db.rollback()

    return {
        "success": True,
        "data": result
    }
