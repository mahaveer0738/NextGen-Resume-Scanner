"""
============================================================
  agents/job_search_agent.py  —  Real Job Search Agent (NEW)

  📌 WHAT DOES THIS AGENT DO?
     Searches for REAL remote job listings using the
     Remotive API — a 100% FREE job board API!
============================================================
"""

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import GOOGLE_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL
from utils.tools import search_real_jobs
import json
import re


def run_job_search_agent(detected_role: str, found_keywords: list) -> dict:
    """
    Searches for real job listings matching the resume profile.
    """

    print(f"💼 Job Search Agent: Finding jobs for '{detected_role}'...")

    top_skills = found_keywords[:3] if found_keywords else []
    search_query = detected_role
    if top_skills:
        search_query += f" {' '.join(top_skills)}"

    print(f"   🔍 Search query: '{search_query}'")

    jobs = search_real_jobs(search_query)

    analysis = None
    if jobs:
        jobs_text = json.dumps(jobs, indent=2)

        prompt = f"""
Based on these REAL job listings found for a "{detected_role}":

JOB LISTINGS:
{jobs_text[:2000]}

CANDIDATE'S SKILLS: {', '.join(found_keywords[:10])}

Analyze the job market for this candidate. Respond ONLY with valid JSON:
{{
  "match_summary": "<2-3 sentences about how well the candidate fits these jobs and the current market>",
  "top_recommendation": "<title of the best matching job from the listings and why it's a good fit>",
  "skills_in_demand": ["top 5 skills mentioned most across these job listings"]
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
                print(f"   ⚠️ Groq job analysis failed ({str(e)}), trying Gemini...")

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
                print(f"   ❌ Gemini job analysis failed: {str(e)}")

        if response_content:
            analysis = _parse_json_response(response_content)

    if not analysis or not analysis.get("match_summary"):
        if jobs:
            top_job = jobs[0].get("title", detected_role)
            company = jobs[0].get("company", "leading companies")
            analysis = {
                "match_summary": f"Strong alignment found with current open market roles for {detected_role}. Your background matches requirements across remote listings.",
                "top_recommendation": f"{top_job} at {company}",
                "skills_in_demand": found_keywords[:5] if found_keywords else ["Problem Solving", "System Architecture", "APIs"]
            }
        else:
            analysis = {
                "match_summary": f"Your profile is well-suited for {detected_role} positions in software and tech.",
                "top_recommendation": f"Senior {detected_role}",
                "skills_in_demand": ["Communication", "Version Control", "Clean Architecture"]
            }

    return {
        "job_listings": jobs,
        "search_query_used": search_query,
        "total_found": len(jobs),
        **analysis
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
