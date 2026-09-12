"""
============================================================
  agents/keyword_agent.py  —  Keyword Analysis Agent (v2.0 ENHANCED)

  📌 WHAT DOES THIS AGENT DO?
     Extracts all technical skills, soft skills, and
     job-specific keywords from the resume. Then compares
     them with what the detected job role typically requires.

     Returns:
     - ✅ Keywords FOUND in resume
     - ❌ Keywords MISSING (common for that role)
     - Match percentage

  📌 v2.0 ENHANCEMENT:
     Now accepts an optional `skills_context` parameter
     from the RAG engine. This provides a FOCUSED view
     of just the skills section, making analysis more accurate.

     Without RAG: LLM reads the entire resume to find skills
     With RAG:    LLM gets a pre-extracted skills section
                  → more accurate, fewer missed keywords
============================================================
"""

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from config import GROQ_API_KEY, GROQ_MODEL
import json
import re

llm = ChatGroq(
    model=GROQ_MODEL,
    groq_api_key=GROQ_API_KEY,
    temperature=0.2
)


def run_keyword_agent(resume_text: str, skills_context: str = "") -> dict:
    """
    Analyzes keywords in the resume.

    📌 v2.0: Now accepts RAG skills context for focused analysis.

    Args:
        resume_text    : Full resume text
        skills_context : (NEW) RAG-extracted skills section text.
                         If provided, the LLM gets a focused view
                         of the skills area for better accuracy.

    Returns:
        dict with found_keywords, missing_keywords, match_percent, detected_role
    """

    # ── Build RAG section for the prompt (v2.0 NEW) ─────────
    # 📌 If RAG provided skills context, include it as a
    #    separate focused section in the prompt.
    #    This helps the LLM zero in on skills without
    #    getting distracted by other resume content.
    rag_section = ""
    if skills_context and skills_context != resume_text:
        rag_section = f"""

FOCUSED SKILLS SECTION (extracted by RAG — pay special attention to this):
------
{skills_context}
------
"""

    prompt = f"""
You are an expert resume keyword analyzer.
Read the resume below and identify the candidate's target job role.

RESUME:
-------
{resume_text}
-------
{rag_section}
Your tasks:
1. Detect the most likely job role (e.g., "Software Engineer", "Data Scientist", "Marketing Manager")
2. List ALL technical and soft skills/keywords FOUND in the resume
3. List important keywords that are MISSING for that role (top 8-10 missing ones)
4. Calculate a match percentage

Respond ONLY with valid JSON in this exact format:
{{
  "detected_role": "<detected job role>",
  "found_keywords": ["keyword1", "keyword2", ...],
  "missing_keywords": ["keyword1", "keyword2", ...],
  "match_percent": <integer 0-100>,
  "total_keywords_found": <integer>
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
            "detected_role": "Unknown",
            "found_keywords": [],
            "missing_keywords": [],
            "match_percent": 0,
            "total_keywords_found": 0
        }
