"""
============================================================
  agents/job_match_agent.py  —  Job Description Matcher

  📌 WHAT DOES THIS AGENT DO?
     The user pastes a Job Description (JD).
     This agent compares the resume against the JD and
     gives a compatibility score + missing skills.

  📌 REAL WORLD USE:
     Before applying to any job, you'd paste the JD here.
     The agent tells you: "You're 72% compatible. You're
     missing Docker and CI/CD experience."
============================================================
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import GOOGLE_API_KEY, GEMINI_MODEL
import json
import re

llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=0.2
)


def run_job_match_agent(resume_text: str, job_description: str) -> dict:
    """
    Compares resume against a job description.

    Args:
        resume_text      : Extracted text from resume
        job_description  : The full job description pasted by user

    Returns:
        dict with compatibility score, matched skills, missing skills
    """

    prompt = f"""
You are a hiring expert. Compare this resume with the job description below.

RESUME:
-------
{resume_text}
-------

JOB DESCRIPTION:
----------------
{job_description}
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

    response = llm.invoke([HumanMessage(content=prompt)])
    return _parse_json_response(response.content)


def _parse_json_response(raw_text: str) -> dict:
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
        return {
            "compatibility_score": 0,
            "label": "Error",
            "matched_requirements": [],
            "missing_requirements": [],
            "recommendation": "Could not analyze. Please try again."
        }
