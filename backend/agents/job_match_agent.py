"""
============================================================
  agents/job_match_agent.py  —  Job Description Matcher (Resilient)

  📌 WHAT DOES THIS AGENT DO?
     The user pastes a Job Description (JD).
     This agent compares the resume against the JD and
     gives a compatibility score + missing skills.
============================================================
"""

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import GOOGLE_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL
import json
import re


def run_job_match_agent(resume_text: str, job_description: str) -> dict:
    """
    Compares resume against a job description.
    """

    prompt = f"""
You are a hiring expert. Compare this resume with the job description below.

RESUME:
-------
{resume_text[:3500]}
-------

JOB DESCRIPTION:
----------------
{job_description[:2500]}
----------------

Analyze:
1. What skills/requirements does the resume MATCH?
2. What important requirements are MISSING from the resume?
3. Overall compatibility score (0-100)

Respond ONLY with valid JSON:
{{
  "compatibility_score": <integer 0-100>,
  "label": "<Strong Match|Good Match|Partial Match|Weak Match>",
  "matched_requirements": ["req1", "req2", ...],
  "missing_requirements": ["req1", "req2", ...],
  "recommendation": "<2-3 sentences on how to improve the resume for this specific job>"
}}
"""

    response_content = None

    if GROQ_API_KEY and GROQ_MODEL:
        try:
            groq_llm = ChatGroq(model=GROQ_MODEL, groq_api_key=GROQ_API_KEY, temperature=0.2, request_timeout=15, max_retries=1)
            response = groq_llm.invoke([HumanMessage(content=prompt)])
            response_content = response.content
        except Exception as e:
            print(f"   ⚠️ Groq job match failed ({str(e)}), trying Gemini...")

    if not response_content and GOOGLE_API_KEY:
        try:
            gemini_llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GOOGLE_API_KEY, temperature=0.2, request_timeout=15, max_retries=1)
            response = gemini_llm.invoke([HumanMessage(content=prompt)])
            response_content = response.content
        except Exception as e:
            print(f"   ❌ Gemini job match fallback failed: {str(e)}")

    if not response_content:
        return _fallback_job_match(resume_text, job_description)

    parsed = _parse_json_response(response_content)
    if not parsed.get("compatibility_score"):
        return _fallback_job_match(resume_text, job_description)
    return parsed


def _fallback_job_match(resume: str, jd: str) -> dict:
    r_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', resume.lower()))
    jd_words = set(re.findall(r'\b[a-zA-Z]{3,}\b', jd.lower()))
    overlap = r_words.intersection(jd_words)
    score = min(90, max(45, int(len(overlap) / max(len(jd_words) * 0.25, 1) * 70)))
    
    return {
        "compatibility_score": score,
        "label": "Good Match" if score >= 70 else "Partial Match",
        "matched_requirements": list(overlap)[:8] if overlap else ["Core Skills", "Experience"],
        "missing_requirements": ["Targeted Industry Keywords", "Framework Alignment"],
        "recommendation": "Tailor your project descriptions to mirror the specific terminology mentioned in the job post."
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
        return {}
