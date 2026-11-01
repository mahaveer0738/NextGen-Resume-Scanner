"""
============================================================
  routes/job_match.py  —  Job Match API Endpoint
============================================================
"""

from typing import Optional
from sqlalchemy.orm import Session
from fastapi import APIRouter, UploadFile, File, Form, Depends
import json

from agents.parser_agent import extract_text_from_file
from agents.job_match_agent import run_job_match_agent
from database import get_db
import models
from utils.auth_utils import get_optional_user

router = APIRouter()


@router.post("/job-match")
async def job_match(
    file: UploadFile = File(...),
    job_description: str = Form(...),
    current_user: Optional[models.User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
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

    # Save to history if logged in
    if current_user:
        try:
            score = result.get("compatibility_score")
            history_record = models.ScanHistory(
                user_id=current_user.id,
                filename=file.filename,
                scan_type="job_match",
                match_percent=float(score) if score is not None else None,
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
