"""
============================================================
  agents/interview_agent.py  —  Interview Questions Generator

  📌 WHAT DOES THIS AGENT DO?
     Reads the resume and target role, then generates
     tailored interview questions that a recruiter might ask
     THIS specific candidate based on their actual experience.
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
    temperature=0.5
)


def run_interview_agent(resume_text: str, job_title: str) -> dict:
    """
    Generates tailored interview questions based on the resume.

    Args:
        resume_text : Extracted resume text
        job_title   : Target role for context

    Returns:
        dict with categorized interview questions
    """

    prompt = f"""
You are an experienced interviewer for {job_title} positions.
Based on the resume below, generate interview questions this candidate might be asked.

RESUME:
-------
{resume_text}
-------

Generate 10 interview questions in 3 categories:
1. Technical questions (based on skills listed in resume)
2. Behavioral questions (based on their experience)
3. Situational questions (for the {job_title} role)

Respond ONLY with valid JSON:
{{
  "technical": [
    {{"question": "<question>", "tip": "<brief answer tip>"}},
    ...
  ],
  "behavioral": [
    {{"question": "<question>", "tip": "<brief answer tip>"}},
    ...
  ],
  "situational": [
    {{"question": "<question>", "tip": "<brief answer tip>"}},
    ...
  ]
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
        return {"technical": [], "behavioral": [], "situational": []}
