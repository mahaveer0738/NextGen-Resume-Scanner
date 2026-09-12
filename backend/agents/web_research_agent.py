"""
============================================================
  agents/web_research_agent.py  —  Web Research Agent (NEW)

  📌 WHAT DOES THIS AGENT DO?
     Uses PREBUILT search tools (DuckDuckGo, Tavily, Wikipedia)
     to research the REAL WORLD about the candidate's role:

     1. 🔍 Searches for TRENDING SKILLS for the detected role
     2. 💰 Looks up SALARY RANGE for the role
     3. 📚 Gets ROLE DESCRIPTION from Wikipedia

     This gives the user REAL, up-to-date information
     instead of just AI-generated guesses.

  📌 WHY DO WE NEED THIS?
     Without web research, our AI only knows what's in
     its training data (which could be outdated).
     With web research, it can tell the user:
     "Hey, GraphQL is trending for Frontend roles in 2025!"

  📌 PREBUILT TOOLS USED:
     - smart_search()    → Tavily (or DuckDuckGo fallback)
     - search_wikipedia() → Wikipedia lookup
     These are imported from utils/tools.py
============================================================
"""

from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage
from config import GROQ_API_KEY, GROQ_MODEL
from utils.tools import smart_search, search_wikipedia
import json
import re


# ─────────────────────────────────────────────
# Initialize the LLM for structuring search results
# ─────────────────────────────────────────────
llm = ChatGroq(
    model=GROQ_MODEL,
    groq_api_key=GROQ_API_KEY,
    temperature=0.3      # Low creativity — we want factual analysis
)


def run_web_research_agent(detected_role: str, found_keywords: list) -> dict:
    """
    Researches the web for industry insights about the detected role.

    📌 HOW THIS AGENT WORKS:
       1. Search the web for trending skills (DuckDuckGo/Tavily)
       2. Search for salary data (DuckDuckGo/Tavily)
       3. Look up the role on Wikipedia for background
       4. Send ALL raw results to Gemini to structure them

    Args:
        detected_role  : The job role detected from the resume
                         (e.g., "Software Engineer", "Data Scientist")
        found_keywords : Skills already found in the resume

    Returns:
        dict with:
          - trending_skills    : Skills currently in demand for this role
          - skills_to_add      : Trending skills NOT on the resume
          - salary_range       : Estimated salary range
          - industry_insights  : Wikipedia summary of the role
          - market_demand      : High/Medium/Low demand indicator
          - search_source      : Which search tools were used
    """

    print(f"🌐 Web Research Agent: Researching '{detected_role}'...")

    # ── STEP 1: Search for trending skills ──────────────────
    # 📌 smart_search() tries Tavily first, falls back to DuckDuckGo
    trending_query = f"most in-demand skills for {detected_role} 2025"
    print(f"   🔍 Searching: {trending_query}")
    trending_raw = smart_search(trending_query)

    # ── STEP 2: Search for salary data ──────────────────────
    salary_query = f"average salary for {detected_role} in India 2025"
    print(f"   🔍 Searching: {salary_query}")
    salary_raw = smart_search(salary_query)

    # ── STEP 3: Get Wikipedia overview of the role ──────────
    # 📌 Wikipedia gives us a reliable description of the role
    print(f"   📚 Looking up: {detected_role} on Wikipedia")
    wiki_raw = search_wikipedia(detected_role)

    # ── STEP 4: Use LLM to structure the raw search data ───
    #
    # 📌 WHY USE LLM HERE?
    #    Raw search results are messy text — snippets, URLs,
    #    random formatting. The LLM reads through all of it
    #    and extracts clean, structured information.
    #
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
    "min": "<estimated minimum annual salary>",
    "max": "<estimated maximum annual salary>",
    "currency": "INR"
  }},
  "industry_insights": "<2-3 sentence summary of the role and current industry trends>",
  "market_demand": "<High|Medium|Low>"
}}
"""

    response = llm.invoke([HumanMessage(content=prompt)])
    result = _parse_json_response(response.content)

    # Add metadata about which search tools were used
    result["search_source"] = "Tavily + DuckDuckGo + Wikipedia"

    return result


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
            "trending_skills": [],
            "skills_to_add": [],
            "salary_range": {"min": "N/A", "max": "N/A", "currency": "INR"},
            "industry_insights": "Could not fetch industry data. Please try again.",
            "market_demand": "Unknown"
        }
