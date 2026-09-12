"""
============================================================
  agents/ats_agent.py  —  ATS Score Calculator Agent

  📌 WHAT IS ATS?
     Applicant Tracking System — software companies use
     to automatically filter resumes BEFORE a human sees
     them. If your resume scores low, it gets rejected
     automatically. Our AI mimics this scoring.

  📌 WHAT DOES THIS AGENT DO?
     1. Takes the extracted resume text
     2. Sends it to Google Gemini with a carefully crafted PROMPT
     3. Gemini analyzes and returns a JSON score + breakdown
     4. We parse and return that score to the frontend

  📌 WHAT IS A PROMPT?
     A "prompt" is the instruction you give to the AI model.
     The quality of your prompt = quality of AI output.
     This is called "Prompt Engineering" — a real skill!
============================================================
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import GOOGLE_API_KEY, GEMINI_MODEL
import json
import re


# ─────────────────────────────────────────────
# INITIALIZE THE LLM (Language Model)
#
# 📌 WHAT IS ChatGoogleGenerativeAI?
#    This is a LangChain "wrapper" around Google's Gemini API.
#    LangChain wraps many different LLMs (GPT, Gemini, Claude)
#    under the SAME interface. So if you ever want to switch
#    from Gemini to GPT-4, you just change ONE line!
# ─────────────────────────────────────────────

llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=0.3      # 0 = very factual/consistent, 1 = creative/random
)


# ─────────────────────────────────────────────
# MAIN FUNCTION: Run ATS Analysis
# ─────────────────────────────────────────────

def run_ats_agent(resume_text: str) -> dict:
    """
    Analyzes the resume for ATS compatibility.

    Args:
        resume_text : Plain text extracted from the resume

    Returns:
        A dict with overall_score, breakdown, and label
    """

    # ── STEP 1: Build the Prompt ──────────────────────────
    # This is the instruction we send to Gemini.
    # We tell it EXACTLY what format to return so we can
    # reliably parse the response.
    prompt = f"""
You are an expert ATS (Applicant Tracking System) analyzer.
Analyze the following resume and give it an ATS compatibility score.

RESUME TEXT:
-----------
{resume_text}
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

    # ── STEP 2: Call Gemini via LangChain ────────────────
    # HumanMessage = a message from the "user" (us) to the AI
    response = llm.invoke([HumanMessage(content=prompt)])

    # ── STEP 3: Parse the JSON response ──────────────────
    return _parse_json_response(response.content)


# ─────────────────────────────────────────────
# PRIVATE HELPER: Safely parse JSON from LLM
# ─────────────────────────────────────────────

def _parse_json_response(raw_text: str) -> dict:
    """
    LLMs sometimes return JSON wrapped in markdown code blocks.
    This function strips that and parses the pure JSON.
    """
    if isinstance(raw_text, list):
        # Extract text from LangChain multimodal message blocks
        raw_text = "".join([block.get("text", "") for block in raw_text if isinstance(block, dict)])
    elif not isinstance(raw_text, str):
        raw_text = str(raw_text)

    # Remove markdown code blocks if present: ```json ... ```
    cleaned = re.sub(r"```(?:json)?", "", raw_text).strip().strip("`").strip()

    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # Fallback: return a safe default if parsing fails
        return {
            "overall_score": 0,
            "label": "Error",
            "breakdown": {},
            "summary": "Could not parse ATS score. Please try again."
        }
