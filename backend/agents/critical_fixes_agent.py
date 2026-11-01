"""
============================================================
  agents/critical_fixes_agent.py  —  Critical Fixes Agent (NEW)

  📌 WHAT DOES THIS AGENT DO?
     This agent ONLY runs when the ATS score is below 50.
     It analyzes the WEAKEST sections of the resume and
     gives URGENT, SPECIFIC fixes that must be done
     before submitting the resume anywhere.
============================================================
"""

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import GOOGLE_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL
import json
import re


def run_critical_fixes_agent(
    resume_text: str,
    ats_result: dict,
    rag_skills_context: str = "",
    rag_experience_context: str = "",
    rag_education_context: str = ""
) -> dict:
    """
    Generates CRITICAL fixes for low-scoring resumes (ATS < 50).
    """

    print("🔧 Critical Fixes Agent: Resume scored LOW — generating urgent fixes...")

    breakdown = ats_result.get("breakdown", {})
    overall_score = ats_result.get("overall_score", 0)

    rag_info = ""
    if rag_skills_context:
        rag_info += f"\n\nSKILLS SECTION (extracted by RAG):\n{rag_skills_context}"
    if rag_experience_context:
        rag_info += f"\n\nEXPERIENCE SECTION (extracted by RAG):\n{rag_experience_context}"
    if rag_education_context:
        rag_info += f"\n\nEDUCATION SECTION (extracted by RAG):\n{rag_education_context}"

    prompt = f"""
You are an URGENT resume repair specialist. This resume scored only {overall_score}/100 on ATS.
It will be REJECTED by most Applicant Tracking Systems without immediate fixes.

ATS SCORE BREAKDOWN (each out of 100):
{json.dumps(breakdown, indent=2)}

FULL RESUME TEXT:
-----------
{resume_text[:3000]}
-----------
{rag_info}

Generate CRITICAL, URGENT fixes. Focus on the LOWEST scoring areas in the breakdown above.
These are not suggestions — these are MUST-DO fixes to prevent automatic rejection.

Respond ONLY with valid JSON:
{{
  "urgency_level": "CRITICAL",
  "overall_diagnosis": "<1-2 sentences explaining WHY this resume is failing ATS>",
  "critical_fixes": [
    {{
      "section": "<formatting|keywords|contact_info|work_experience|education>",
      "current_score": <score from breakdown>,
      "issue": "<exactly what's wrong>",
      "fix": "<specific action to take>",
      "example": "<before/after example>",
      "priority": "<P0-Must Fix|P1-Important|P2-Nice to Have>"
    }}
  ],
  "estimated_score_after_fixes": <integer 65-90>
}}
"""

    response_content = None

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
            print(f"   ⚠️ Groq critical fixes failed ({str(e)}), falling back to Gemini...")

    if not response_content and GOOGLE_API_KEY:
        try:
            gemini_llm = ChatGoogleGenerativeAI(
                model=GEMINI_MODEL,
                google_api_key=GOOGLE_API_KEY,
                temperature=0.2,
                request_timeout=15,
                max_retries=1
            )
            response = gemini_llm.invoke([HumanMessage(content=prompt)])
            response_content = response.content
        except Exception as e:
            print(f"   ❌ Gemini critical fixes fallback failed: {str(e)}")

    if not response_content:
        return _fallback_critical_fixes(overall_score)

    parsed = _parse_json_response(response_content)
    if not parsed.get("critical_fixes"):
        return _fallback_critical_fixes(overall_score)
    return parsed


def _fallback_critical_fixes(score: int) -> dict:
    return {
        "urgency_level": "CRITICAL",
        "overall_diagnosis": f"The resume scored {score}/100 and lacks core formatting and quantified bullet points required by ATS filters.",
        "critical_fixes": [
            {
                "section": "work_experience",
                "current_score": 35,
                "issue": "Missing quantified metrics and impact statements in job bullets.",
                "fix": "Rewrite bullets using the XYZ formula: Accomplished [X] as measured by [Y], by doing [Z].",
                "example": "Change 'Built web app' to 'Engineered high-performance web app serving 1,000+ daily active users'.",
                "priority": "P0-Must Fix"
            },
            {
                "section": "keywords",
                "current_score": 40,
                "issue": "Low density of industry-standard tools and frameworks.",
                "fix": "Incorporate key industry technologies directly into project descriptions and skills header.",
                "example": "Explicitly list Git, REST APIs, SQL, and primary programming languages.",
                "priority": "P0-Must Fix"
            },
            {
                "section": "formatting",
                "current_score": 50,
                "issue": "Section headers might not conform to standard ATS labels.",
                "fix": "Use standard labels: 'Work Experience', 'Education', 'Technical Skills', 'Projects'.",
                "example": "Avoid creative section names like 'Where I have been' or 'My Journey'.",
                "priority": "P1-Important"
            }
        ],
        "estimated_score_after_fixes": 78
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
        return {"critical_fixes": []}
