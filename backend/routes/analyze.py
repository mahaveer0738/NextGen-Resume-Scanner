"""
============================================================
  routes/analyze.py  —  Resume Analysis API Endpoint

  📌 WHAT IS AN ENDPOINT / ROUTE?
     An endpoint is a URL that the frontend can call.
     Think of it like a phone extension number —
     each extension does something different.

     POST /api/analyze  ← This is the endpoint
     The frontend sends a file to this URL,
     and gets back the AI analysis as JSON.

  📌 WHAT IS @router.post()?
     It's a DECORATOR. It tells FastAPI:
     "When someone sends a POST request to /analyze,
      run the function below it."

  📌 WHAT IS UploadFile?
     FastAPI's built-in type for handling file uploads.
     It gives us the file name, size, and raw bytes.
============================================================
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from agents.parser_agent import extract_text_from_file
from graph.resume_graph import run_resume_analysis
from config import MAX_FILE_SIZE_BYTES


# ─────────────────────────────────────────────
# CREATE A ROUTER
#
# 📌 A Router is like a "mini FastAPI app".
#    We create one per feature area, then
#    register all of them in main.py
# ─────────────────────────────────────────────
router = APIRouter()


# ─────────────────────────────────────────────
# ENDPOINT: POST /api/analyze
#
# 📌 HOW THE FRONTEND CALLS THIS:
#    const formData = new FormData();
#    formData.append("file", selectedFile);
#    fetch("/api/analyze", { method: "POST", body: formData })
# ─────────────────────────────────────────────

@router.post("/analyze")
async def analyze_resume(file: UploadFile = File(...)):
    """
    Main resume analysis endpoint.

    Accepts: A PDF or DOCX file upload
    Returns: JSON with ATS score, keywords, and suggestions
    """

    # ── STEP 1: Validate file size ──────────────────────
    file_bytes = await file.read()   # Read the raw bytes

    if len(file_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=413,
            detail=f"File too large. Maximum size is 5MB."
        )

    # ── STEP 2: Extract text using Parser Agent ──────────
    resume_text = extract_text_from_file(file_bytes, file.filename)

    # ── STEP 3: Run the LangGraph Pipeline ──────────────
    # This kicks off the full multi-agent workflow!
    result = run_resume_analysis(resume_text)

    # ── STEP 4: Return JSON to the frontend ──────────────
    return {
        "success": True,
        "filename": file.filename,
        "data": result
    }
