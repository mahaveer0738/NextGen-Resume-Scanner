"""
============================================================
  main.py  —  The ENTRY POINT of the ResumeAI backend (v2.1)

  📌 WHAT'S NEW IN v2.1?
     - JWT Authentication routes (/api/auth/*)
     - Scan History routes (/api/history)
     - Database initialization on startup (SQLite)
     - CORS updated to support Authorization headers

  📌 HOW TO RUN:
     cd backend
     uvicorn main:app --reload --port 8000

     Then open: http://localhost:8000/docs
============================================================
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all route files
from routes import analyze, job_match, cover_letter, interview
from routes import auth, history

# Database setup — creates tables if they don't exist
from database import engine, Base
import models  # noqa: F401 — must import so models register with Base


# ─────────────────────────────────────────────
# CREATE DATABASE TABLES ON STARTUP
#
# 📌 create_all() checks if tables exist and
#    creates them if they don't. It will NOT
#    drop or overwrite existing tables — safe!
# ─────────────────────────────────────────────
Base.metadata.create_all(bind=engine)
print("[OK] Database tables initialized (SQLite)")


# ─────────────────────────────────────────────
# CREATE THE FASTAPI APP INSTANCE
# ─────────────────────────────────────────────
app = FastAPI(
    title="ResumeAI Backend",
    description="AI-powered resume analysis API using LangGraph + Gemini (v2.1 — with JWT Auth & History)",
    version="2.1.0"
)


# ─────────────────────────────────────────────
# CORS MIDDLEWARE
#
# 📌 Updated for JWT authentication:
#    - allow_credentials=True  (needed for auth headers)
#    - allow_origins uses specific origin list
#      (cannot be ["*"] when credentials=True)
#    - Allow "Authorization" header explicitly
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5500",
        "http://127.0.0.1:5500",
        "http://localhost:5501",
        "http://127.0.0.1:5501",
        "null",            # For file:// opened HTML files (index.html opened directly)
        "*"                # Development mode — remove in production
    ],
    allow_credentials=False,  # Keep False since we include "*" in origins
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─────────────────────────────────────────────
# REGISTER ROUTE FILES
# ─────────────────────────────────────────────

# Core AI features
app.include_router(analyze.router,       prefix="/api", tags=["Resume Analysis"])
app.include_router(job_match.router,     prefix="/api", tags=["Job Match"])
app.include_router(cover_letter.router,  prefix="/api", tags=["Cover Letter"])
app.include_router(interview.router,     prefix="/api", tags=["Interview"])

# Authentication (NEW v2.1)
app.include_router(auth.router,          prefix="/api", tags=["Authentication"])

# History (NEW v2.1)
app.include_router(history.router,       prefix="/api", tags=["History"])


# ─────────────────────────────────────────────
# ROOT ENDPOINT — Health Check
# ─────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "ResumeAI Backend is running! 🚀",
        "version": "2.1.0",
        "features": ["JWT Auth", "Scan History", "LangGraph AI Pipeline"],
        "docs": "Visit /docs to explore the API"
    }
