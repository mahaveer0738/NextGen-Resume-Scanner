"""
============================================================
  routes/history.py  —  Scan History API Endpoints

  📌 WHAT IS THIS?
     API routes to retrieve a user's past resume analyses.
     Each time a logged-in user analyzes a resume, the
     result is saved to the database. These endpoints let
     them view that history.

  📌 ENDPOINTS:
     GET  /api/history          — List all past scans (paginated)
     GET  /api/history/{id}     — Get full result of one scan
     DELETE /api/history/{id}   — Delete a specific scan record
     DELETE /api/history        — Clear all history
============================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import json

from database import get_db
import models
from utils.auth_utils import get_current_user

router = APIRouter()


# ─────────────────────────────────────────────
# PYDANTIC SCHEMAS
# ─────────────────────────────────────────────

class ScanHistoryListItem(BaseModel):
    """
    Compact scan summary for the list view.
    (We don't return the full_result in the list — too heavy)
    """
    id:            int
    filename:      str
    scan_type:     str
    ats_score:     Optional[float]
    detected_role: Optional[str]
    match_percent: Optional[float]
    created_at:    datetime

    class Config:
        from_attributes = True


class ScanHistoryDetail(ScanHistoryListItem):
    """Full scan detail including the JSON result."""
    full_result: Optional[dict]  # Parsed from JSON string in DB

    class Config:
        from_attributes = True


# ─────────────────────────────────────────────
# ENDPOINT: GET /api/history
# ─────────────────────────────────────────────

@router.get("/history", response_model=List[ScanHistoryListItem])
def get_history(
    limit: int = 20,
    offset: int = 0,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns a paginated list of the user's past resume scans.
    Most recent scans come first.

    Query params:
        limit  : How many to return (default 20)
        offset : How many to skip (for pagination)
    """
    scans = (
        db.query(models.ScanHistory)
        .filter(models.ScanHistory.user_id == current_user.id)
        .order_by(models.ScanHistory.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return scans


# ─────────────────────────────────────────────
# ENDPOINT: GET /api/history/{id}
# ─────────────────────────────────────────────

@router.get("/history/{scan_id}")
def get_history_detail(
    scan_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Returns the full result of a specific past scan.
    Only the owner can access their own scans.
    """
    scan = (
        db.query(models.ScanHistory)
        .filter(
            models.ScanHistory.id == scan_id,
            models.ScanHistory.user_id == current_user.id
        )
        .first()
    )

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found."
        )

    # Parse JSON string back to dict
    full_result = None
    if scan.full_result:
        try:
            full_result = json.loads(scan.full_result)
        except (json.JSONDecodeError, TypeError):
            full_result = None

    return {
        "id":            scan.id,
        "filename":      scan.filename,
        "scan_type":     scan.scan_type,
        "ats_score":     scan.ats_score,
        "detected_role": scan.detected_role,
        "match_percent": scan.match_percent,
        "created_at":    scan.created_at,
        "full_result":   full_result
    }


# ─────────────────────────────────────────────
# ENDPOINT: DELETE /api/history/{id}
# ─────────────────────────────────────────────

@router.delete("/history/{scan_id}", status_code=204)
def delete_history_item(
    scan_id: int,
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a specific scan record.
    Only the owner can delete their own records.
    """
    scan = (
        db.query(models.ScanHistory)
        .filter(
            models.ScanHistory.id == scan_id,
            models.ScanHistory.user_id == current_user.id
        )
        .first()
    )

    if not scan:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found."
        )

    db.delete(scan)
    db.commit()
    return None


# ─────────────────────────────────────────────
# ENDPOINT: DELETE /api/history (clear all)
# ─────────────────────────────────────────────

@router.delete("/history", status_code=204)
def clear_history(
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete ALL scan history for the current user.
    """
    db.query(models.ScanHistory).filter(
        models.ScanHistory.user_id == current_user.id
    ).delete()
    db.commit()
    return None

