"""
============================================================
  models.py  —  SQLAlchemy Database Models

  📌 WHAT ARE MODELS?
     Models are Python classes that map to database tables.
     Each attribute becomes a column in the table.

  📌 TABLES WE CREATE:
     1. users         — stores registered user accounts
     2. scan_history  — stores resume analysis results per user
============================================================
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Float
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
from database import Base


# ─────────────────────────────────────────────
# USER MODEL
# Stores registered user accounts
# ─────────────────────────────────────────────
class User(Base):
    __tablename__ = "users"

    id         = Column(Integer, primary_key=True, index=True)
    username   = Column(String(50),  unique=True, nullable=False, index=True)
    email      = Column(String(100), unique=True, nullable=False, index=True)
    full_name  = Column(String(100), nullable=True)
    hashed_password = Column(String(200), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # One user → many scan history records
    scan_history = relationship("ScanHistory", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User id={self.id} username={self.username}>"


# ─────────────────────────────────────────────
# SCAN HISTORY MODEL
# Stores every resume analysis result for a user
# ─────────────────────────────────────────────
class ScanHistory(Base):
    __tablename__ = "scan_history"

    id             = Column(Integer, primary_key=True, index=True)
    user_id        = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Resume metadata
    filename       = Column(String(255), nullable=False)
    scan_type      = Column(String(50),  default="full_analysis")  # full_analysis | job_match | cover_letter | interview

    # Key metrics (for quick list view)
    ats_score      = Column(Float, nullable=True)
    detected_role  = Column(String(100), nullable=True)
    match_percent  = Column(Float, nullable=True)

    # Full result stored as JSON string
    full_result    = Column(Text, nullable=True)   # JSON.dumps of the full API response

    # Timestamps
    created_at     = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationship back to user
    user           = relationship("User", back_populates="scan_history")

    def __repr__(self):
        return f"<ScanHistory id={self.id} user_id={self.user_id} ats={self.ats_score}>"

