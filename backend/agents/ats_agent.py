"""
============================================================
  agents/ats_agent.py  —  ATS Score Calculator Agent (Resilient)

  📌 WHAT IS ATS?
     Applicant Tracking System — software companies use
     to automatically filter resumes BEFORE a human sees
     them. If your resume scores low, it gets rejected
     automatically. Our AI mimics this scoring.

  📌 RESILIENCE FEATURES:
     1. Tries Groq (lightning fast Llama-3.1)
     2. Falls back to Google Gemini (gemini-1.5-flash)
     3. Fallback heuristic scoring if both APIs are unavailable
     4. Strict 15-second timeout and max_retries=1 to prevent hanging
============================================================
"""

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import GOOGLE_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL
import json
import re


def run_ats_agent(resume_text: str) -> dict:
    """
    Analyzes the resume for ATS compatibility.

    Args:
        resume_text : Plain text extracted from the resume

    Returns:
        A dict with overall_score, breakdown, label, and summary
    """

    prompt = f"""
You are an expert ATS (Applicant Tracking System) analyzer.
Analyze the following resume and give it an ATS compatibility score.

RESUME TEXT:
-----------
{resume_text[:4000]}
-----------

Evaluate the resume on these 5 criteria:
1. formatting         - Is it clean, simple, parseable by ATS software?
2. keywords           - Does it contain industry-relevant keywords?
3. contact_info       - Does it have email, phone, LinkedIn?
4. work_experience    - Are achievements quantified? Action verbs used?
5. education          - Is education section clearly present?

Respond ONLY with valid JSON in this exact format (no extra text):
{{
  "overall_score": <integer 0-100>,
  "label": "<Excellent|Good|Average|Needs Work>",
  "breakdown": {{
    "formatting": <integer 0-100>,
    "keywords": <integer 0-100>,
    "contact_info": <integer 0-100>,
    "work_experience": <integer 0-100>,
    "education": <integer 0-100>
  }},
  "summary": "<One sentence about the resume's ATS readiness>"
}}
"""

    response_content = None

    # ── TRY 1: Groq (ultra fast) ──────────────────────────
    if GROQ_API_KEY and GROQ_MODEL:
        try:
            groq_llm = ChatGroq(
                model=GROQ_MODEL,
                groq_api_key=GROQ_API_KEY,
                temperature=0.2,
                request_timeout=15,
                max_retries=1
            )
            response = groq_llm.invoke([HumanMessage(content=prompt)])
            response_content = response.content
        except Exception as e:
            print(f"   ⚠️ Groq ATS scoring failed ({str(e)}), trying Gemini...")

    # ── TRY 2: Gemini fallback ───────────────────────────
    if not response_content and GOOGLE_API_KEY:
        try:
            gemini_llm = ChatGoogleGenerativeAI(
                model=GEMINI_MODEL,
                google_api_key=GOOGLE_API_KEY,
                temperature=0.3,
                request_timeout=15,
                max_retries=1
            )
            response = gemini_llm.invoke([HumanMessage(content=prompt)])
            response_content = response.content
        except Exception as e:
            print(f"   ⚠️ Gemini ATS scoring failed: {str(e)}")

    # ── TRY 3: Parse response or use heuristic fallback ──
    if response_content:
        parsed = _parse_json_response(response_content)
        if parsed.get("overall_score", 0) > 0:
            return parsed

    # ── HEURISTIC FALLBACK: Computes realistic score from actual resume text ──
    print("   ℹ️ Using built-in ATS heuristic evaluation...")
    return _compute_heuristic_ats(resume_text)


def _compute_heuristic_ats(text: str) -> dict:
    """
    Computes a realistic ATS score and breakdown by analyzing
    structural elements of the resume text directly.
    """
    lower = text.lower()
    
    # Contact Info Check (up to 100)
    has_email = bool(re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text))
    has_phone = bool(re.search(r'(\+?\d[\d\s\-\(\)]{8,}\d)', text))
    has_linkedin = "linkedin.com" in lower or "github.com" in lower
    contact_score = 40 + (25 if has_email else 0) + (20 if has_phone else 0) + (15 if has_linkedin else 0)

    # Education Check (up to 100)
    edu_terms = ["bachelor", "master", "degree", "university", "college", "b.tech", "b.e", "b.sc", "m.tech", "diploma", "gpa", "cgpa"]
    edu_matches = sum(1 for term in edu_terms if term in lower)
    edu_score = min(100, 50 + edu_matches * 15)

    # Work Experience Check (up to 100)
    action_verbs = ["developed", "built", "managed", "created", "designed", "implemented", "led", "engineered", "improved", "optimized", "increased", "reduced"]
    verb_matches = sum(1 for v in action_verbs if v in lower)
    has_numbers = len(re.findall(r'\b\d+[%+k]?\b', text))
    exp_score = min(100, 40 + min(verb_matches * 5, 30) + min(has_numbers * 3, 30))

    # Formatting Check (up to 100)
    word_count = len(text.split())
    if 250 <= word_count <= 1000:
        fmt_score = 85
    elif word_count > 1000:
        fmt_score = 70
    else:
        fmt_score = 55

    # Keywords Check (up to 100)
    tech_keywords = [
        "python", "java", "javascript", "react", "node", "sql", "aws", "docker",
        "git", "html", "css", "c++", "linux", "api", "rest", "ci/cd", "agile",
        "machine learning", "data", "testing", "cloud", "mongodb", "fastapi"
    ]
    kw_found = sum(1 for kw in tech_keywords if kw in lower)
    kw_score = min(100, 45 + kw_found * 6)

    overall = round((contact_score * 0.15) + (edu_score * 0.15) + (exp_score * 0.30) + (fmt_score * 0.15) + (kw_score * 0.25))

    if overall >= 80:
        label = "Excellent"
    elif overall >= 65:
        label = "Good"
    elif overall >= 50:
        label = "Average"
    else:
        label = "Needs Work"

    return {
        "overall_score": overall,
        "label": label,
        "breakdown": {
            "formatting": fmt_score,
            "keywords": kw_score,
            "contact_info": contact_score,
            "work_experience": exp_score,
            "education": edu_score
        },
        "summary": f"Resume scored {overall}/100 based on parsed structure, key action verbs, and section coverage."
    }


def _parse_json_response(raw_text: str) -> dict:
    if isinstance(raw_text, list):
        raw_text = "".join([block.get("text", "") for block in raw_text if isinstance(block, dict)])
    elif not isinstance(raw_text, str):
        raw_text = str(raw_text)

    cleaned = re.sub(r"```(?:json)?", "", raw_text).strip().strip("`").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except Exception:
                pass
        return {
            "overall_score": 0,
            "label": "Error",
            "breakdown": {},
            "summary": "Could not parse ATS score."
        }
