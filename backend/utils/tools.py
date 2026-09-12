"""
============================================================
  utils/tools.py  —  Prebuilt Tools Registry

  📌 WHAT ARE TOOLS IN AI?
     Tools give AI agents the ability to INTERACT with
     the real world — search the internet, call APIs,
     read databases, etc.

     Without tools: AI can only "think" (generate text)
     With tools:    AI can "act" (search, fetch, compute)

  📌 TOOLS IN THIS FILE:
     ┌──────────────────────────────────────────────────┐
     │  1. DuckDuckGo  → Free web search (no API key!)  │
     │  2. Tavily      → AI-optimized search (free tier) │
     │  3. Wikipedia   → Knowledge lookup (free)         │
     │  4. Remotive    → Real job listings (100% FREE!)  │
     └──────────────────────────────────────────────────┘

  📌 SMART FALLBACK SYSTEM:
     If Tavily API key is missing → falls back to DuckDuckGo
     ALL other tools are 100% free, no keys needed!
     This means the app works even without any paid API keys!

  📌 HOW DO WE USE THEM?
     Each tool is a function that agents call inside their
     LangGraph nodes. The agents don't "decide" to call
     tools — our code calls them directly (Approach A).
============================================================
"""

import requests
from config import TAVILY_API_KEY


# ═════════════════════════════════════════════
#  TOOL 1: DuckDuckGo Search (100% FREE)
#
#  📌 WHY DUCKDUCKGO?
#     - No API key needed AT ALL
#     - No usage limits
#     - Returns real web search results
#     - Perfect as a fallback when Tavily is missing
#
#  📌 HOW IT WORKS:
#     Uses the duckduckgo-search Python library which
#     programmatically searches DuckDuckGo and returns
#     results as structured data.
# ═════════════════════════════════════════════

def get_duckduckgo_tool():
    """
    Returns a LangChain DuckDuckGoSearchResults tool.

    📌 This is a PREBUILT tool from langchain-community.
       You don't write the search logic — LangChain
       already wrote it for you! You just import and use.
    """
    from langchain_community.tools import DuckDuckGoSearchResults
    return DuckDuckGoSearchResults(max_results=5)


def search_with_duckduckgo(query: str) -> str:
    """
    Searches the web using DuckDuckGo.

    Args:
        query : What to search for (e.g., "top Python skills 2025")

    Returns:
        String with search results (titles + snippets + URLs)
    """
    try:
        tool = get_duckduckgo_tool()
        result = tool.invoke(query)
        return str(result)
    except Exception as e:
        print(f"   ⚠️ DuckDuckGo search failed: {str(e)}")
        return f"Search failed: {str(e)}"


# ═════════════════════════════════════════════
#  TOOL 2: Tavily Search (AI-Optimized)
#
#  📌 WHAT IS TAVILY?
#     Tavily is a search engine BUILT specifically for
#     AI agents. Unlike Google/DuckDuckGo which return
#     messy HTML pages, Tavily returns clean, structured
#     results that AI can easily understand.
#
#  📌 WHY IS IT BETTER FOR AI?
#     - Returns clean text (no HTML parsing needed)
#     - Filters out ads and irrelevant content
#     - Optimized for factual accuracy
#     - Free tier: 1000 searches/month (plenty!)
#
#  📌 HOW TO GET YOUR API KEY:
#     1. Go to https://tavily.com
#     2. Click "Get API Key" (sign up free)
#     3. Copy the key from your dashboard
#     4. Paste in backend/.env:  TAVILY_API_KEY=tvly-xxxxx
# ═════════════════════════════════════════════

def get_tavily_tool():
    """
    Returns a Tavily search tool, or None if no API key.

    📌 GRACEFUL FALLBACK:
       If TAVILY_API_KEY is empty in .env, this returns None.
       The smart_search() function then falls back to DuckDuckGo.
    """
    if not TAVILY_API_KEY:
        print("   ⚠️ Tavily API key not found — will use DuckDuckGo instead")
        return None

    try:
        from langchain_community.tools.tavily_search import TavilySearchResults
        return TavilySearchResults(max_results=5, api_key=TAVILY_API_KEY)
    except Exception as e:
        print(f"   ⚠️ Tavily init failed: {str(e)}") 
        return None


def search_with_tavily(query: str) -> str:
    """
    Searches using Tavily. If Tavily is unavailable, falls back to DuckDuckGo.

    📌 FALLBACK CHAIN:
       Tavily (best for AI) → DuckDuckGo (free backup)
    """
    tool = get_tavily_tool()
    if tool:
        try:
            result = tool.invoke(query)
            return str(result)
        except Exception as e:
            print(f"   ⚠️ Tavily search failed: {str(e)}, falling back to DuckDuckGo")

    # Fallback to DuckDuckGo
    return search_with_duckduckgo(query)


# ═════════════════════════════════════════════
#  TOOL 3: Wikipedia (Knowledge Base)
#
#  📌 WHY WIKIPEDIA?
#     When analyzing a resume for a role like "Data Scientist",
#     we can look up what a Data Scientist actually does,
#     what skills are typically required, what the industry
#     looks like — all from Wikipedia.
#
#     Free, reliable, no API key needed!
#
#  📌 HOW THE TOOL WORKS:
#     Uses the wikipedia Python library to query Wikipedia's
#     API and return article summaries.
# ═════════════════════════════════════════════

def get_wikipedia_tool():
    """
    Returns a LangChain Wikipedia lookup tool.

    📌 Another PREBUILT tool from langchain-community.
       Wrapper around the Wikipedia API.
    """
    from langchain_community.tools import WikipediaQueryRun
    from langchain_community.utilities import WikipediaAPIWrapper

    api_wrapper = WikipediaAPIWrapper(
        top_k_results=2,             # Return top 2 Wikipedia articles
        doc_content_chars_max=1500   # Limit response size (tokens are $$$)
    )
    return WikipediaQueryRun(api_wrapper=api_wrapper)


def search_wikipedia(query: str) -> str:
    """
    Looks up a topic on Wikipedia.

    Args:
        query : Topic to look up (e.g., "Machine Learning Engineer")

    Returns:
        Wikipedia summary text (up to 1500 chars)
    """
    try:
        tool = get_wikipedia_tool()
        result = tool.invoke(query)
        return str(result)
    except Exception as e:
        print(f"   ⚠️ Wikipedia lookup failed: {str(e)}")
        return f"Wikipedia lookup failed: {str(e)}"


# ═════════════════════════════════════════════
#  TOOL 4: Remotive API (Real Job Listings)
#
#  📌 WHAT IS REMOTIVE?
#     Remotive is a 100% FREE job board API that lists
#     REAL remote jobs from companies like GitLab,
#     Shopify, Automattic, InVision, and many more!
#
#  📌 WHY REMOTIVE INSTEAD OF JSEARCH?
#     - 100% FREE — no API key needed AT ALL!
#     - No registration, no sign-up, no RapidAPI account
#     - Returns real, current job listings
#     - Focuses on tech/dev roles (perfect for our audience)
#     - Simple REST API: just send a GET request!
#
#  📌 HOW IT WORKS:
#     API endpoint: https://remotive.com/api/remote-jobs
#     Parameters:
#       - search   : job title (e.g., "python developer")
#       - limit    : max results (e.g., 5)
#     That's it! No headers, no auth, no keys!
#
#  📌 EXAMPLE API CALL:
#     GET https://remotive.com/api/remote-jobs?search=python&limit=5
#     Returns JSON with real jobs including title, company, URL
# ═════════════════════════════════════════════

def search_real_jobs(query: str, location: str = "Remote", num_results: int = 5) -> list:
    """
    Searches for REAL job listings using Remotive API (100% FREE).

    📌 NO API KEY NEEDED! Just works out of the box.
       Returns real remote job listings from companies like
       GitLab, Shopify, Automattic, and hundreds of others.

    Args:
        query       : Job title to search (e.g., "Python Developer")
        location    : Not used by Remotive (always remote), kept for
                      compatibility with the job_search_agent interface
        num_results : How many jobs to return (default 5)

    Returns:
        List of dicts with job details:
        [{title, company, location, type, url, description}, ...]
        Returns empty list if API fails (graceful fallback).
    """

    # ── Build the API request ───────────────────────────────
    # 📌 Notice: NO API key, NO headers, NO authentication!
    #    This is what makes Remotive so developer-friendly.
    url = "https://remotive.com/api/remote-jobs"

    params = {
        "search": query,
        "limit": num_results
    }

    # ── Make the API call ───────────────────────────────────
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()   # Raises exception for 4xx/5xx errors

        # Parse the response
        # 📌 Remotive returns: { "jobs": [ {job1}, {job2}, ... ] }
        data = response.json().get("jobs", [])[:num_results]

        # Extract the important fields from each job listing
        jobs = []
        for job in data:
            # 📌 Clean the description — Remotive returns HTML,
            #    so we strip tags for clean text display
            raw_desc = job.get("description", "")
            # Simple HTML tag removal (strip <tags>)
            import re
            clean_desc = re.sub(r'<[^>]+>', '', raw_desc)[:200]

            jobs.append({
                "title":       job.get("title", "N/A"),
                "company":     job.get("company_name", "N/A"),
                "location":    job.get("candidate_required_location", "Remote"),
                "type":        job.get("job_type", "full_time"),
                "url":         job.get("url", ""),
                "description": (clean_desc + "...") if clean_desc else "No description",
                "category":    job.get("category", "N/A"),
                "salary":      job.get("salary", "Not specified"),
                "posted_date": job.get("publication_date", "N/A")
            })

        print(f"   💼 Remotive: Found {len(jobs)} real remote job listings")
        return jobs

    except requests.exceptions.RequestException as e:
        print(f"   ❌ Remotive API error: {str(e)}")
        return []
    except Exception as e:
        print(f"   ❌ Remotive unexpected error: {str(e)}")
        return []


# ═════════════════════════════════════════════
#  SMART SEARCH: Uses the best available tool
#
#  📌 FALLBACK CHAIN:
#     Tavily (best) → DuckDuckGo (free backup)
#
#     This way, the app ALWAYS works:
#     - Have Tavily key? Uses Tavily (better results)
#     - No Tavily key?   Uses DuckDuckGo (still works!)
# ═════════════════════════════════════════════

def smart_search(query: str) -> str:
    """
    Searches the web using the best available tool.
    Tries Tavily first (AI-optimized), falls back to DuckDuckGo (free).

    Args:
        query : What to search for

    Returns:
        Search results as a string
    """
    return search_with_tavily(query)  # Has built-in DuckDuckGo fallback
