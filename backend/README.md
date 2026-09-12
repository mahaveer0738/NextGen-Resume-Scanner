# ResumeAI Backend — Setup Guide

## What is this?
The Python AI backend for ResumeAI. It uses **LangGraph** to orchestrate multiple
**Gemini AI agents** that analyze resumes and return structured results.

---

## Technology Stack

| Tool | Purpose |
|---|---|
| **FastAPI** | Python web framework — creates the API |
| **LangGraph** | Orchestrates multiple AI agents in a workflow |
| **LangChain** | Interface layer to talk to Gemini AI |
| **Google Gemini** | The actual LLM (AI brain) |
| **pdfplumber** | Reads text from PDF files |
| **python-docx** | Reads text from DOCX files |

---

## Quick Start

### Step 1 — Install Python dependencies
```bash
cd backend
pip install -r requirements.txt
```

### Step 2 — Add your Gemini API Key
1. Go to https://aistudio.google.com/app/apikey
2. Create a free API key
3. Open `.env` file and replace the placeholder:
```
GOOGLE_API_KEY=your_actual_key_here
```

### Step 3 — Start the backend server
```bash
uvicorn main:app --reload --port 8000
```

### Step 4 — Test the API
Open your browser and go to:
```
http://localhost:8000/docs
```
You'll see a beautiful interactive API explorer!

---

## API Endpoints

| Method | URL | What it does |
|---|---|---|
| GET | `/` | Health check |
| POST | `/api/analyze` | Analyze resume → ATS score + keywords + suggestions |
| POST | `/api/job-match` | Compare resume vs job description |
| POST | `/api/cover-letter` | Generate cover letter |
| POST | `/api/interview-questions` | Generate interview questions |

---

## Folder Structure Explained

```
backend/
├── main.py              ← App entry point, starts FastAPI
├── config.py            ← Reads API keys from .env
├── requirements.txt     ← Python package list
├── .env                 ← YOUR API KEY (never commit this!)
├── .gitignore           ← Files to exclude from git
│
├── agents/              ← Each file = one AI agent
│   ├── parser_agent.py          (extracts text from files)
│   ├── ats_agent.py             (calculates ATS score)
│   ├── keyword_agent.py         (finds keywords)
│   ├── suggestions_agent.py     (gives improvement tips)
│   ├── job_match_agent.py       (resume vs JD comparison)
│   ├── cover_letter_agent.py    (generates cover letters)
│   └── interview_agent.py       (generates interview questions)
│
├── graph/               ← LangGraph workflow
│   └── resume_graph.py          (connects all agents)
│
├── routes/              ← API endpoints (URLs)
│   ├── analyze.py               (POST /api/analyze)
│   ├── job_match.py             (POST /api/job-match)
│   ├── cover_letter.py          (POST /api/cover-letter)
│   └── interview.py             (POST /api/interview-questions)
│
└── utils/               ← Shared helper functions
    └── helpers.py
```
