"""
============================================================
  config.py  —  All configuration / settings in one place

  📌 WHY A SEPARATE CONFIG FILE?
     Instead of hardcoding your API key in every file
     (which is dangerous!), we read it ONCE from the .env
     file and share it across the whole project.

  📌 WHAT IS python-dotenv?
     It reads key=value pairs from your .env file
     and makes them available as environment variables.
     So your API key never shows up in your source code!
============================================================
"""

import os
from dotenv import load_dotenv

# Load variables from the .env file into environment
load_dotenv()


# ─────────────────────────────────────────────
# API KEYS
# ─────────────────────────────────────────────

# Your Google Gemini API Key (get it free at https://aistudio.google.com)
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "") 

# The Gemini model to use for all agents
GEMINI_MODEL = "gemini-3.8-flash"     # Free tier — fast & capable

# Your Groq API Key (get it free at https://console.groq.com/keys)
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

# The Groq model to use for lightweight agents
GROQ_MODEL = "groq/compound-mini" # Fast model available on your specific account tier


# ─────────────────────────────────────────────
# SEARCH API KEYS (v2.0 — NEW)
#
# 📌 Only Tavily is optional — everything else is FREE!
#    - No Tavily key? → DuckDuckGo is used instead (free)
#    - Remotive (job search) → 100% free, no key needed!
#    - Wikipedia → free, no key needed!
#    - DuckDuckGo → free, no key needed!
# ─────────────────────────────────────────────

# Tavily — AI-optimized search (free tier: 1000 searches/month)
# Get your key at: https://tavily.com
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY", "")


# ─────────────────────────────────────────────
# RAG SETTINGS (v2.0 — NEW)
#
# 📌 These control how the resume is split and indexed
#    for RAG (Retrieval Augmented Generation).
# ─────────────────────────────────────────────

RAG_CHUNK_SIZE    = 500    # Characters per chunk (500 ≈ 100 words)
RAG_CHUNK_OVERLAP = 100    # Overlap between chunks (prevents cutting mid-sentence)


# ─────────────────────────────────────────────
# CONDITIONAL BRANCHING THRESHOLD (v2.0 — NEW)
#
# 📌 If the ATS score is below this number, the graph
#    routes to the Critical Fixes Agent for urgent help.
# ─────────────────────────────────────────────

ATS_CRITICAL_THRESHOLD = 50   # Score below this → critical fixes agent runs


# ─────────────────────────────────────────────
# FILE UPLOAD SETTINGS
# ─────────────────────────────────────────────

# Maximum file size: 5 MB (same as your frontend validation)
MAX_FILE_SIZE_MB = 5
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# Allowed file types
ALLOWED_EXTENSIONS = {".pdf", ".doc", ".docx"}


# ─────────────────────────────────────────────
# APP SETTINGS
# ─────────────────────────────────────────────

APP_TITLE       = "ResumeAI"
APP_VERSION     = "2.0.0"       # Updated to v2.0!
DEBUG_MODE      = True     # Set to False in production
