"""
============================================================
  agents/suggestions_agent.py  —  AI Suggestions Agent

  📌 WHAT DOES THIS AGENT DO?
     Reads the ATS score + resume text and generates
     SPECIFIC, ACTIONABLE improvement suggestions.
     Not generic tips — actual advice based on THIS resume.
     Includes automatic Gemini fallback if Groq encounters issues.
============================================================
"""

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import GROQ_API_KEY, GROQ_MODEL, GOOGLE_API_KEY, GEMINI_MODEL
import json
import re


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
{resume_text[:4000]}
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
    }}
  ]
}}
"""

    response_content = None

    # Try Groq first for high-speed generation
    if GROQ_API_KEY and GROQ_MODEL:
        try:
            groq_llm = ChatGroq(
                model=GROQ_MODEL,
                groq_api_key=GROQ_API_KEY,
                temperature=0.4,
                request_timeout=15,
                max_retries=1
            )
            response = groq_llm.invoke([HumanMessage(content=prompt)])
            response_content = response.content
        except Exception as e:
            print(f"   ⚠️ Groq suggestion generation failed ({str(e)}), falling back to Gemini...")

    # Fallback to Google Gemini
    if not response_content and GOOGLE_API_KEY:
        try:
            gemini_llm = ChatGoogleGenerativeAI(
                model=GEMINI_MODEL,
                google_api_key=GOOGLE_API_KEY,
                temperature=0.4,
                request_timeout=15,
                max_retries=1
            )
            response = gemini_llm.invoke([HumanMessage(content=prompt)])
            response_content = response.content
        except Exception as e:
            print(f"   ❌ Gemini suggestion fallback failed: {str(e)}")

    if not response_content:
        return _fallback_suggestions(ats_score)

    parsed = _parse_json_response(response_content)
    if not parsed.get("suggestions"):
        return _fallback_suggestions(ats_score)
    return parsed


def _fallback_suggestions(ats_score: int) -> dict:
    return {
        "suggestions": [
            {
                "title": "Quantify Achievements with Metrics",
                "description": "Add measurable numbers, percentages, and outcomes to your work bullets (e.g. 'Improved API response time by 35%').",
                "priority": "High"
            },
            {
                "title": "Strengthen Technical Skills Section",
                "description": "Group your technologies by category (Languages, Frameworks, Cloud, Databases) for faster ATS and recruiter scanning.",
                "priority": "High"
            },
            {
                "title": "Lead with Strong Action Verbs",
                "description": "Start each experience bullet with impactful verbs like Engineered, Architected, Automated, or Spearheaded instead of 'Responsible for'.",
                "priority": "Medium"
            },
            {
                "title": "Add LinkedIn and GitHub Links",
                "description": "Ensure clean, clickable hyperlinks to your GitHub portfolio and LinkedIn profile are present in the contact header.",
                "priority": "Medium"
            },
            {
                "title": "Align Keywords with Target Role",
                "description": "Review job postings for your target title and weave common industry terms naturally throughout your experience.",
                "priority": "Low"
            }
        ]
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
        return {"suggestions": []}
