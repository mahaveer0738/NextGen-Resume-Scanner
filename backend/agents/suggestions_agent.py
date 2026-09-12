"""
============================================================
  agents/suggestions_agent.py  —  AI Suggestions Agent

  📌 WHAT DOES THIS AGENT DO?
     Reads the ATS score + resume text and generates
     SPECIFIC, ACTIONABLE improvement suggestions.
     Not generic tips — actual advice based on THIS resume.
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
    temperature=0.4      # Slightly creative for helpful suggestions
)


def run_suggestions_agent(resume_text: str, ats_score: int) -> dict:
    """
    Generates personalized improvement suggestions.

    Args:
        resume_text : Extracted resume text
        ats_score   : The ATS score from ats_agent (used as context)

    Returns:
        dict with a list of improvement suggestions
    """

    prompt = f"""
You are a professional resume coach. The resume below scored {ats_score}/100 on ATS.

RESUME:
-------
{resume_text}
-------

Give 6 specific, actionable improvement suggestions for this resume.
Be SPECIFIC — mention exact sections or content that needs fixing.

Respond ONLY with valid JSON:
{{
  "suggestions": [
    {{
      "title": "<short title of the suggestion>",
      "description": "<specific advice in 1-2 sentences>",
      "priority": "<High|Medium|Low>"
    }},
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
        return {"suggestions": []}
