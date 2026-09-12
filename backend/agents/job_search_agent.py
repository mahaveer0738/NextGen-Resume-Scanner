"""
============================================================
  agents/job_search_agent.py  —  Real Job Search Agent (NEW)

  📌 WHAT DOES THIS AGENT DO?
     Searches for REAL remote job listings using the
     Remotive API — a 100% FREE job board API!

     After analyzing the resume, this agent finds actual
     jobs that match the candidate's profile — with real
     company names, locations, and apply links!

  📌 WHY IS THIS POWERFUL?
     Most resume analyzers just give you a score.
     Ours actually says: "Here are 5 real jobs you
     can apply to RIGHT NOW based on your resume."

  📌 API USED: Remotive (100% FREE — no API key!)
     - No registration needed
     - No API key needed
     - Returns real remote job listings
     - From companies like GitLab, Shopify, Automattic
============================================================
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import GOOGLE_API_KEY, GEMINI_MODEL
from utils.tools import search_real_jobs
import json
import re


# ─────────────────────────────────────────────
# Initialize LLM for job market analysis
# ─────────────────────────────────────────────
llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=0.2      # Very factual — we're analyzing real data
)


def run_job_search_agent(detected_role: str, found_keywords: list) -> dict:
    """
    Searches for real job listings matching the resume profile.

    📌 HOW THIS AGENT WORKS:
       1. Build a smart search query from role + top skills
       2. Call JSearch API to get real job listings
       3. Use LLM to analyze how well the candidate fits
       4. Return jobs + market analysis

    Args:
        detected_role  : The detected job role (e.g., "Data Scientist")
        found_keywords : Skills found in the resume

    Returns:
        dict with:
          - job_listings      : List of real jobs [{title, company, url, ...}]
          - search_query_used : The query sent to JSearch
          - total_found       : Number of jobs found
          - match_summary     : AI-generated summary of job market fit
          - top_recommendation: Best matching job and why
          - skills_in_demand  : Skills mentioned most in job listings
    """

    print(f"💼 Job Search Agent: Finding jobs for '{detected_role}'...")

    # ── STEP 1: Build a smart search query ──────────────────
    #
    # 📌 Instead of just searching "Software Engineer",
    #    we include top skills for more relevant results:
    #    "Software Engineer Python React AWS"
    #
    top_skills = found_keywords[:3] if found_keywords else []
    search_query = detected_role
    if top_skills:
        search_query += f" {' '.join(top_skills)}"

    print(f"   🔍 Search query: '{search_query}'")

    # ── STEP 2: Search for real jobs using JSearch API ──────
    #
    # 📌 search_real_jobs() is defined in utils/tools.py
    #    It calls the JSearch API on RapidAPI and returns
    #    a list of job dicts. Returns [] if no API key.
    #
    jobs = search_real_jobs(search_query)

    # ── STEP 3: Use LLM to analyze the job market ──────────
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
        response = llm.invoke([HumanMessage(content=prompt)])
        analysis = _parse_json_response(response.content)
    else:
        # No jobs found (Remotive API might be down)
        analysis = {
            "match_summary": "No job listings found. The Remotive API might be temporarily unavailable — try again later.",
            "top_recommendation": "N/A — Remotive API returned no results",
            "skills_in_demand": []
        }

    # ── STEP 4: Combine everything ──────────────────────────
    return {
        "job_listings":      jobs,
        "search_query_used": search_query,
        "total_found":       len(jobs),
        **analysis   # Unpacks match_summary, top_recommendation, skills_in_demand
    }


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
            "match_summary": "Could not analyze job market.",
            "top_recommendation": "N/A",
            "skills_in_demand": []
        }
