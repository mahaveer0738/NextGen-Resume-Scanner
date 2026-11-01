"""
============================================================
  agents/cover_letter_agent.py  —  Cover Letter Generator (Resilient)

  📌 WHAT DOES THIS AGENT DO?
     Takes the resume + target job title and generates a
     professional, personalized cover letter.
============================================================
"""

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import GOOGLE_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL
import json
import re


def run_cover_letter_agent(resume_text: str, job_title: str, company_name: str = "") -> dict:
    """
    Generates a personalized cover letter.
    """

    company_line = f"at {company_name}" if company_name else ""

    prompt = f"""
You are a professional cover letter writer.
Write a compelling cover letter for a {job_title} position {company_line}.
Base it on the candidate's actual experience from their resume.

RESUME:
-------
{resume_text[:3500]}
-------

Write a 3-4 paragraph professional cover letter that:
1. Opens with an engaging hook
2. Highlights 2-3 most relevant experiences from the resume
3. Shows enthusiasm for the role
4. Closes with a confident call to action

Respond ONLY with valid JSON:
{{
  "cover_letter": "<the full cover letter text with proper line breaks>",
  "word_count": <integer>,
  "key_highlights_used": ["highlight1", "highlight2", "highlight3"]
}}
"""

    response_content = None

    if GROQ_API_KEY and GROQ_MODEL:
        try:
            groq_llm = ChatGroq(model=GROQ_MODEL, groq_api_key=GROQ_API_KEY, temperature=0.5, request_timeout=15, max_retries=1)
            response = groq_llm.invoke([HumanMessage(content=prompt)])
            response_content = response.content
        except Exception as e:
            print(f"   ⚠️ Groq cover letter failed ({str(e)}), trying Gemini...")

    if not response_content and GOOGLE_API_KEY:
        try:
            gemini_llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GOOGLE_API_KEY, temperature=0.5, request_timeout=15, max_retries=1)
            response = gemini_llm.invoke([HumanMessage(content=prompt)])
            response_content = response.content
        except Exception as e:
            print(f"   ❌ Gemini cover letter fallback failed: {str(e)}")

    if not response_content:
        return _fallback_cover_letter(job_title, company_name)

    parsed = _parse_json_response(response_content)
    if not parsed.get("cover_letter"):
        return _fallback_cover_letter(job_title, company_name)
    return parsed


def _fallback_cover_letter(job_title: str, company: str) -> dict:
    target_co = company if company else "your esteemed organization"
    text = (
        f"Dear Hiring Team,\n\n"
        f"I am writing to express my strong interest in the {job_title} position at {target_co}. "
        f"With a strong foundation in modern software development and engineering best practices, "
        f"I am excited about the opportunity to contribute to your team's mission and technical initiatives.\n\n"
        f"Throughout my career and academic background, I have focused on designing efficient solutions, "
        f"collaborating across cross-functional teams, and continuously improving code quality. "
        f"My hands-on experience aligns closely with the technical and collaborative requirements needed for this role.\n\n"
        f"I welcome the opportunity to discuss how my skills and background can add immediate value to {target_co}. "
        f"Thank you for your time and consideration.\n\n"
        f"Sincerely,\nCandidate"
    )
    return {
        "cover_letter": text,
        "word_count": len(text.split()),
        "key_highlights_used": ["Hands-on engineering skills", "Collaboration & cross-functional work", "Proactive problem solving"]
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
