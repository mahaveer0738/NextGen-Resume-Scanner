"""
============================================================
  agents/critical_fixes_agent.py  —  Critical Fixes Agent (NEW)

  📌 WHAT DOES THIS AGENT DO?
     This agent ONLY runs when the ATS score is below 50.
     It analyzes the WEAKEST sections of the resume and
     gives URGENT, SPECIFIC fixes that must be done
     before submitting the resume anywhere.

  📌 WHY A SEPARATE AGENT? (Not just more suggestions?)
     Regular suggestions = "Nice to have" improvements
     Critical fixes = "MUST DO or your resume gets rejected"

     Think of it like a car inspection:
     Suggestions = "You could upgrade your tires"
     Critical fixes = "YOUR BRAKES ARE BROKEN, DON'T DRIVE!"

  📌 THIS IS CONDITIONAL BRANCHING IN ACTION:
     In the LangGraph, this node is reached via a
     conditional edge from the ATS node:

     ┌────────────┐       ┌──────────────────────┐
     │  ATS Node  │─<50──→│  Critical Fixes Node  │
     │  (score)   │       │  (this agent!)        │
     └────────────┘       └──────────────────────┘
          │ ≥50
          ▼
     ┌────────────┐
     │ Suggestions│  (skips critical fixes)
     └────────────┘

  📌 USES RAG CONTEXT:
     Instead of analyzing the full resume, this agent uses
     RAG-extracted sections (skills, experience, education)
     to focus on the WEAKEST areas identified by ATS.
============================================================
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import GOOGLE_API_KEY, GEMINI_MODEL
import json
import re


# ─────────────────────────────────────────────
# Initialize LLM
# ─────────────────────────────────────────────
llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=0.3      # Precise and factual for critical fixes
)


def run_critical_fixes_agent(
    resume_text: str,
    ats_result: dict,
    rag_skills_context: str = "",
    rag_experience_context: str = "",
    rag_education_context: str = ""
) -> dict:
    """
    Generates CRITICAL fixes for low-scoring resumes (ATS < 50).

    📌 THIS AGENT ONLY RUNS WHEN ATS SCORE < 50
       It's triggered by the conditional edge in the LangGraph.
       If ATS score >= 50, this function is never called.

    Uses RAG context to give SECTION-SPECIFIC fixes instead
    of generic advice.

    Args:
        resume_text            : Full resume text
        ats_result             : Results from ATS agent (score + breakdown)
        rag_skills_context     : RAG-extracted skills section text
        rag_experience_context : RAG-extracted experience section text
        rag_education_context  : RAG-extracted education section text

    Returns:
        dict with:
          - urgency_level             : Always "CRITICAL"
          - overall_diagnosis         : Why the resume is failing
          - critical_fixes            : List of urgent fixes
          - estimated_score_after_fixes: Predicted score if fixes are applied
    """

    print("🔧 Critical Fixes Agent: Resume scored LOW — generating urgent fixes...")

    # ── Get the ATS breakdown to identify weakest areas ─────
    breakdown = ats_result.get("breakdown", {})
    overall_score = ats_result.get("overall_score", 0)

    # ── Build RAG context section ───────────────────────────
    # 📌 RAG gives us FOCUSED text for each section.
    #    Instead of the AI reading the entire resume,
    #    it reads only the relevant extracted sections.
    rag_info = ""
    if rag_skills_context:
        rag_info += f"\n\nSKILLS SECTION (extracted by RAG):\n{rag_skills_context}"
    if rag_experience_context:
        rag_info += f"\n\nEXPERIENCE SECTION (extracted by RAG):\n{rag_experience_context}"
    if rag_education_context:
        rag_info += f"\n\nEDUCATION SECTION (extracted by RAG):\n{rag_education_context}"

    # ── Build the prompt ────────────────────────────────────
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
      "section": "<which section: formatting/keywords/contact_info/work_experience/education>",
      "current_score": <score from breakdown for this section>,
      "issue": "<exactly what's wrong in this section>",
      "fix": "<specific action to take — be very precise, not generic>",
      "example": "<show a before/after example if possible>",
      "priority": "<P0-Must Fix|P1-Important|P2-Nice to Have>"
    }}
  ],
  "estimated_score_after_fixes": <estimated new ATS score if all fixes applied, integer 0-100>
}}

Generate 4-6 critical fixes, ordered by priority (P0 first).
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    return _parse_json_response(response.content)


# ─────────────────────────────────────────────
# PRIVATE HELPER: Safely parse JSON from LLM
# ─────────────────────────────────────────────

def _parse_json_response(raw_text: str) -> dict:
    """Safely parse JSON from LLM response."""
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
            "urgency_level": "CRITICAL",
            "overall_diagnosis": "Could not generate critical fixes. Please try again.",
            "critical_fixes": [],
            "estimated_score_after_fixes": 0
        }
