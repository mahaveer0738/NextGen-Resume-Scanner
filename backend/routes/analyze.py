"""
============================================================
  routes/analyze.py  —  Resume Analysis API Endpoint (v2.1)

  📌 WHAT'S NEW IN v2.1?
     - JWT authentication support (optional)
     - If user is logged in → save result to scan_history DB
     - If user is a guest   → still works, result not saved
     - Returns user info in response when authenticated

  📌 ENDPOINT:
     POST /api/analyze
     Headers (optional): Authorization: Bearer <token>
     Body: multipart/form-data with "file" field
============================================================
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import Optional
import json

from agents.parser_agent import extract_text_from_file
from graph.resume_graph import run_resume_analysis
from config import MAX_FILE_SIZE_BYTES
from database import get_db
import models
from utils.auth_utils import get_optional_user

router = APIRouter()


@router.post("/analyze")
async def analyze_resume(
    file: UploadFile = File(...),
    current_user: Optional[models.User] = Depends(get_optional_user),
    db: Session = Depends(get_db)
):
    """
    Main resume analysis endpoint.

    Accepts: A PDF or DOCX file upload
    Returns: JSON with ATS score, keywords, suggestions, jobs, etc.

    If user is authenticated (JWT token provided):
    - Saves the full result to scan_history table
    - Returns scan_id in the response (for history lookup)
    """

    # ── STEP 1: Validate file size ──────────────────────
    file_bytes = await file.read()

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail="File too large. Maximum size is 5MB."
        )

    # ── STEP 2: Extract text using Parser Agent ──────────
    resume_text = extract_text_from_file(file_bytes, file.filename)

    # ── STEP 3: Run the LangGraph Pipeline ──────────────
    result = run_resume_analysis(resume_text)

    # ── STEP 4: Save to history if user is logged in ────
    scan_id = None
    if current_user:
        try:
            # Extract key metrics for quick summary columns
            ats_score     = result.get("ats", {}).get("overall_score")
            detected_role = result.get("keywords", {}).get("detected_role")
            match_percent = result.get("keywords", {}).get("match_percent")

            history_record = models.ScanHistory(
                user_id       = current_user.id,
                filename      = file.filename,
                scan_type     = "full_analysis",
                ats_score     = ats_score,
                detected_role = detected_role,
                match_percent = match_percent,
                full_result   = json.dumps(result)
            )
            db.add(history_record)
            db.commit()
            db.refresh(history_record)
            scan_id = history_record.id
            print(f"   💾 Saved scan history #{scan_id} for user '{current_user.username}'")
        except Exception as e:
            print(f"   ⚠️ Failed to save history: {e}")
            # Don't fail the whole request if history save fails
            db.rollback()

    # ── STEP 5: Return JSON to the frontend ──────────────
    response = {
        "success": True,
        "filename": file.filename,
        "data": result
    }

    if current_user:
        response["scan_id"]  = scan_id
        response["username"] = current_user.username

    return response
