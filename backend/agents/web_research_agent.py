"""
============================================================
  agents/web_research_agent.py  —  Web Research Agent (NEW)

  📌 WHAT DOES THIS AGENT DO?
     Uses PREBUILT search tools (DuckDuckGo, Tavily, Wikipedia)
     to research the REAL WORLD about the candidate's role:
     1. Trending skills
     2. Salary range
     3. Role description
============================================================
"""

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import GROQ_API_KEY, GROQ_MODEL, GOOGLE_API_KEY, GEMINI_MODEL
from utils.tools import smart_search, search_wikipedia
import json
import re


def run_web_research_agent(detected_role: str, found_keywords: list) -> dict:
    """
    Researches the web for industry insights about the detected role.
    """

    print(f"🌐 Web Research Agent: Researching '{detected_role}'...")

    # Step 1: Trending skills
    trending_query = f"top in demand skills {detected_role} 2025 2026"
    trending_raw = smart_search(trending_query)

    # Step 2: Salary search
    salary_query = f"{detected_role} average salary India LPA Glassdoor AmbitionBox"
    salary_raw = smart_search(salary_query)

    # Step 3: Wikipedia overview
    wiki_raw = search_wikipedia(detected_role)

    prompt = f"""
You are a career research analyst. Based on the web search results below,
extract structured information about the "{detected_role}" role.

SEARCH RESULTS - TRENDING SKILLS:
{trending_raw[:1500]}

SEARCH RESULTS - SALARY:
{salary_raw[:1000]}

WIKIPEDIA OVERVIEW:
{wiki_raw[:1000]}

SKILLS ALREADY ON RESUME: {', '.join(found_keywords[:15])}

Based on these search results, respond ONLY with valid JSON:
{{
  "trending_skills": ["skill1", "skill2", "skill3", "skill4", "skill5"],
  "skills_to_add": ["skills from trending_skills that are NOT already on the resume"],
  "salary_range": {{
    "min": "<estimated minimum annual salary (include units like 'LPA' for INR or 'k' for USD)>",
    "max": "<estimated maximum annual salary (include units like 'LPA' for INR or 'k' for USD)>",
    "currency": "INR"
  }},
  "industry_insights": "<2-3 sentence summary of the role and current industry trends>",
  "market_demand": "<High|Medium|Low>"
}}
"""

    response_content = None

    if GROQ_API_KEY and GROQ_MODEL:
        try:
            groq_llm = ChatGroq(model=GROQ_MODEL, groq_api_key=GROQ_API_KEY, temperature=0.3, request_timeout=15, max_retries=1)
            response = groq_llm.invoke([HumanMessage(content=prompt)])
            response_content = response.content
        except Exception as e:
            print(f"   ⚠️ Groq web research analysis failed ({str(e)}), falling back to Gemini...")

    if not response_content and GOOGLE_API_KEY:
        try:
            gemini_llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GOOGLE_API_KEY, temperature=0.3, request_timeout=15, max_retries=1)
            response = gemini_llm.invoke([HumanMessage(content=prompt)])
            response_content = response.content
        except Exception as e:
            print(f"   ❌ Gemini web research fallback failed: {str(e)}")

    if not response_content:
        return {
            "trending_skills": [],
            "skills_to_add": [],
            "salary_range": {"min": "N/A", "max": "N/A", "currency": "INR"},
            "industry_insights": "Could not fetch industry data. Please try again.",
            "market_demand": "Unknown",
            "search_source": "Offline Fallback"
        }

    result = _parse_json_response(response_content)
    result["search_source"] = "Tavily + DuckDuckGo + Wikipedia"
    return result


def _parse_json_response(raw_text: str) -> dict:
    """Safely parse JSON from LLM response."""
    if isinstance(raw_text, list):
        raw_text = "".join([block.get("text", "") for block in raw_text if isinstance(block, dict)])
    elif not isinstance(raw_text, str):
        raw_text = str(raw_text)

    cleaned = re.sub(r"```(?:json)?", "", raw_text).strip().strip("`").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        return {
            "trending_skills": [],
            "skills_to_add": [],
            "salary_range": {"min": "N/A", "max": "N/A", "currency": "INR"},
            "industry_insights": "Could not fetch industry data. Please try again.",
            "market_demand": "Unknown"
        }
