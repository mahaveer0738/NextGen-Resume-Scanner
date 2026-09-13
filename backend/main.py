"""
============================================================
  main.py  —  The ENTRY POINT of the ResumeAI backend

  📌 WHAT IS FastAPI?
     FastAPI is a Python framework that lets you create
     an API (Application Programming Interface) —
     basically a "bridge" between your frontend (HTML/JS)
     and your AI agents (Python code).

     Think of it like a waiter in a restaurant:
       - Frontend (customer) sends an ORDER (HTTP request)
       - FastAPI (waiter) carries it to the KITCHEN (agents)
       - Kitchen processes it and FastAPI brings back the FOOD (JSON response)

  📌 WHY FastAPI and not Flask?
     - FastAPI is ASYNC (handles multiple users at once)
     - Auto-generates API docs at /docs (super helpful)
     - Built-in data validation using Pydantic models
     - Much faster for AI/ML workloads

  📌 HOW TO RUN THIS FILE:
     cd backend
     uvicorn main:app --reload --port 8000

     Then open: http://localhost:8000/docs
     You'll see a beautiful auto-generated API explorer!
============================================================
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import all route files (we will create these one by one)
from routes import analyze, job_match, cover_letter, interview


# ─────────────────────────────────────────────
# CREATE THE FASTAPI APP INSTANCE
# ─────────────────────────────────────────────
app = FastAPI(
    title="ResumeAI Backend",
    description="AI-powered resume analysis API using LangGraph + Gemini",
    version="1.0.0"
)


# ─────────────────────────────────────────────
# CORS MIDDLEWARE
#
# 📌 WHAT IS CORS?
#    When your frontend (index.html) tries to call
#    the backend API, the browser BLOCKS it by default
#    because they are on different "origins" (ports).
#    CORS middleware tells the browser: "Hey, it's okay,
#    allow requests from the frontend!"
# ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # Allow all origins (fine for development)
    allow_credentials=False,      # Must be False when allow_origins=["*"]
    allow_methods=["*"],          # Allow GET, POST, PUT, DELETE etc.
    allow_headers=["*"],          # Allow all headers
)


# ─────────────────────────────────────────────
# REGISTER ROUTE FILES
#
# 📌 WHAT ARE ROUTERS?
#    Instead of putting ALL endpoints in one big file,
#    we split them into separate files (routes/).
#    Each router handles one "topic" of the API.
# ─────────────────────────────────────────────
app.include_router(analyze.router,       prefix="/api", tags=["Resume Analysis"])
app.include_router(job_match.router,     prefix="/api", tags=["Job Match"])
app.include_router(cover_letter.router,  prefix="/api", tags=["Cover Letter"])
app.include_router(interview.router,     prefix="/api", tags=["Interview"])


# ─────────────────────────────────────────────
# ROOT ENDPOINT — Health Check
# ─────────────────────────────────────────────
@app.get("/")
def root():
    return {
        "message": "ResumeAI Backend is running! 🚀",
        "docs": "Visit /docs to explore the API"
    }
