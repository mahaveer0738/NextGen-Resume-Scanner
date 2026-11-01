"""
============================================================
  routes/cover_letter.py  —  Cover Letter API Endpoint
============================================================
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, UploadFile, File, Form, Depends
import json

from agents.parser_agent import extract_text_from_file
from agents.cover_letter_agent import run_cover_letter_agent
from database import get_db
import models
from utils.auth_utils import get_optional_user

router = APIRouter()


@router.post("/cover-letter")
async def generate_cover_letter(
    file: UploadFile = File(...),
    job_title: str = Form(...),
    company_name: str = Form(""),     # Optional — empty string by default
    current_user: Optional[models.User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
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

    # Save to history if logged in
    if current_user:
        try:
            history_record = models.ScanHistory(
                user_id=current_user.id,
                filename=file.filename,
                scan_type="cover_letter",
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
