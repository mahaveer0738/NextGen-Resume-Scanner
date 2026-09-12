"""
============================================================
  graph/resume_graph.py  —  The Enhanced LangGraph Workflow v2.0

  📌 WHAT CHANGED FROM v1.0?

     v1.0 (OLD):
     ───────────
     Linear pipeline: ATS → Keywords → Suggestions → END
     - Simple and sequential
     - No web search, no real jobs
     - No conditional logic

     v2.0 (NEW — THIS FILE):
     ────────────────────────
     Smart pipeline with:
       ✅ RAG indexing (smart resume section querying)
       ✅ Parallel execution (ATS + Keywords run simultaneously)
       ✅ Conditional branching (low score → critical fixes agent)
       ✅ Web research tools (DuckDuckGo, Tavily, Wikipedia)
       ✅ Real job listings (JSearch API)
       ✅ Fan-in / Join (both branches → aggregator)

  📌 v2.0 GRAPH FLOW:

                      ┌──→ [ats_node] ──→ {score<50?} ──→ [critical_fixes] ──→ [suggestions] ──┐
     [parse_node] ────┤                          │ ≥50                                           ├──→ [aggregator] → END
                      │                          └────────→ [suggestions] ──────────────────────┘
                      └──→ [keyword_node] ──→ [web_research] ──→ [job_search] ──────────────────┘

  📌 KEY CONCEPTS USED:

     ┌──────────────────────────────────────────────────────────────┐
     │  PARALLEL FAN-OUT                                            │
     │  parse_node → ats_node + keyword_node (run simultaneously)   │
     │  Both branches process the resume in different ways          │
     └──────────────────────────────────────────────────────────────┘
     ┌──────────────────────────────────────────────────────────────┐
     │  CONDITIONAL EDGES                                           │
     │  ats_node → {if score < 50} → critical_fixes_node           │
     │  ats_node → {if score >= 50} → suggestions_node (skip fixes)│
     └──────────────────────────────────────────────────────────────┘
     ┌──────────────────────────────────────────────────────────────┐
     │  FAN-IN / JOIN                                               │
     │  aggregator_node waits for BOTH branches to complete         │
     │  before combining all results into one response              │
     └──────────────────────────────────────────────────────────────┘
     ┌──────────────────────────────────────────────────────────────┐
     │  RAG CONTEXT                                                 │
     │  parse_node creates embeddings, pre-queries key sections     │
     │  Other nodes use focused sections instead of full resume     │
     └──────────────────────────────────────────────────────────────┘
============================================================
"""

from typing import TypedDict, Optional
from langgraph.graph import StateGraph, END

# ── Agent imports ──────────────────────────────────────────
from agents.ats_agent import run_ats_agent
from agents.keyword_agent import run_keyword_agent
from agents.suggestions_agent import run_suggestions_agent
from agents.critical_fixes_agent import run_critical_fixes_agent
from agents.web_research_agent import run_web_research_agent
from agents.job_search_agent import run_job_search_agent

# ── RAG import ─────────────────────────────────────────────
from utils.rag_engine import ResumeRAGEngine

# ── Config import ──────────────────────────────────────────
from config import ATS_CRITICAL_THRESHOLD


# ═════════════════════════════════════════════
#  STEP 1: DEFINE THE STATE (EXPANDED for v2.0)
#
#  📌 WHAT CHANGED?
#     v1.0 had 5 fields (input + 3 agents + final)
#     v2.0 has 11 fields:
#       + 3 RAG context fields (skills, experience, education)
#       + 3 new agent result fields (critical_fixes, web_research, job_search)
#
#  📌 WHY MORE STATE FIELDS?
#     Each new node in the graph needs its own state field
#     to write results to. The state is like a shared form —
#     more agents = more fields on the form.
# ═════════════════════════════════════════════

class ResumeState(TypedDict):

    # ── INPUT ──────────────────────────────────────────────
    resume_text: str                         # Raw text from the resume file

    # ── RAG CONTEXT (v2.0 NEW) ─────────────────────────────
    # 📌 These are PRE-QUERIED sections from the RAG engine.
    #    Instead of sending the full resume to every agent,
    #    we query for specific sections and send only what's relevant.
    #
    #    Think of it like: instead of giving a 50-page book
    #    to every reader, you give each reader only the
    #    chapter they need.
    #
    rag_skills_context:      Optional[str]   # RAG-extracted skills section
    rag_experience_context:  Optional[str]   # RAG-extracted experience section
    rag_education_context:   Optional[str]   # RAG-extracted education section

    # ── AGENT RESULTS (existing from v1.0) ─────────────────
    ats_result:              Optional[dict]  # Output from ATS agent
    keyword_result:          Optional[dict]  # Output from Keyword agent
    suggestions_result:      Optional[dict]  # Output from Suggestions agent

    # ── AGENT RESULTS (v2.0 NEW) ───────────────────────────
    critical_fixes_result:   Optional[dict]  # Only filled if ATS score < 50
    web_research_result:     Optional[dict]  # Trending skills, salary, insights
    job_search_result:       Optional[dict]  # Real job listings from JSearch

    # ── FINAL OUTPUT ───────────────────────────────────────
    final_result:            Optional[dict]  # Everything combined


# ═════════════════════════════════════════════
#  STEP 2: DEFINE THE NODES (Agent Functions)
#
#  📌 v2.0 has 7 nodes (up from 4 in v1.0):
#     1. parse_node          → RAG indexing + section extraction
#     2. ats_node            → ATS scoring (PARALLEL with #3)
#     3. keyword_node        → Keyword extraction (PARALLEL with #2)
#     4. critical_fixes_node → Urgent fixes (CONDITIONAL — only if score < 50)
#     5. suggestions_node    → Improvement tips
#     6. web_research_node   → DuckDuckGo + Tavily + Wikipedia
#     7. job_search_node     → JSearch API real listings
#     8. aggregator_node     → Combines everything
# ═════════════════════════════════════════════


def parse_node(state: ResumeState) -> dict:
    """
    Node 0: Parse + RAG Indexing (ENTRY POINT — v2.0 NEW)

    📌 WHAT'S NEW:
       In v1.0, parsing happened in the route handler.
       In v2.0, this node ALSO builds a RAG index:

       1. Takes the resume text
       2. Splits into chunks (RecursiveCharacterTextSplitter)
       3. Generates embeddings (Google embedding-001)
       4. Stores in FAISS vector store
       5. Pre-queries for key sections (skills, experience, education)
       6. Stores the queried sections in state for other nodes

    Reads:  state["resume_text"]
    Writes: rag_skills_context, rag_experience_context, rag_education_context
    """
    print("📄 Parse Node: Building RAG index from resume...")
    resume_text = state["resume_text"]

    try:
        # ── Build the RAG engine ────────────────────────────
        # This creates the FAISS vector store with embeddings
        rag = ResumeRAGEngine(resume_text)

        # ── Pre-query for key sections ──────────────────────
        # 📌 We query NOW so that downstream nodes don't need
        #    to rebuild the RAG engine. The relevant sections
        #    are stored in state and passed along.
        skills_ctx = rag.query(
            "technical skills, programming languages, frameworks, tools, technologies"
        )
        experience_ctx = rag.query(
            "work experience, projects, achievements, responsibilities, accomplishments"
        )
        education_ctx = rag.query(
            "education, degree, university, certifications, courses, training"
        )

        print("   ✅ RAG index built — sections extracted successfully")

    except Exception as e:
        # ── Graceful fallback ───────────────────────────────
        # 📌 If RAG fails (e.g., resume too short, API error),
        #    we fall back to using the full resume text.
        #    The pipeline continues without RAG.
        print(f"   ⚠️ RAG failed ({str(e)}), using full text as fallback")
        skills_ctx     = resume_text
        experience_ctx = resume_text
        education_ctx  = resume_text

    return {
        "rag_skills_context":     skills_ctx,
        "rag_experience_context": experience_ctx,
        "rag_education_context":  education_ctx,
    }


def ats_node(state: ResumeState) -> dict:
    """
    Node 1: ATS Analysis

    📌 PARALLEL EXECUTION:
       This node runs SIMULTANEOUSLY with keyword_node!
       Both start right after parse_node completes.
       LangGraph handles this automatically when you add
       two edges from the same source node.

    Reads:  state["resume_text"]
    Writes: state["ats_result"]
    """
    print("🔢 ATS Node: Analyzing ATS compatibility...")
    result = run_ats_agent(state["resume_text"])
    return {"ats_result": result}


def keyword_node(state: ResumeState) -> dict:
    """
    Node 2: Keyword Analysis (v2.0 ENHANCED)

    📌 PARALLEL EXECUTION:
       Runs SIMULTANEOUSLY with ats_node!

    📌 v2.0 ENHANCEMENT:
       Now uses RAG skills context instead of just the full resume.
       The RAG engine pre-extracted the skills section in parse_node,
       so the keyword agent gets a focused view of just the skills.

    Reads:  state["resume_text"], state["rag_skills_context"]
    Writes: state["keyword_result"]
    """
    print("🔑 Keyword Node: Extracting keywords (with RAG context)...")

    # Use RAG skills context for focused analysis
    # Falls back to full resume if RAG context isn't available
    skills_context = state.get("rag_skills_context") or state["resume_text"]

    result = run_keyword_agent(state["resume_text"], skills_context)
    return {"keyword_result": result}


def critical_fixes_node(state: ResumeState) -> dict:
    """
    Node 3a: Critical Fixes (v2.0 NEW — CONDITIONAL)

    📌 CONDITIONAL BRANCHING:
       This node ONLY runs when ATS score < 50.
       The route_after_ats() function decides whether
       this node runs or is skipped.

       If ATS score < 50:
         ats_node → THIS NODE → suggestions_node
       If ATS score >= 50:
         ats_node → suggestions_node (this node is SKIPPED)

    📌 USES RAG CONTEXT:
       Gets the pre-extracted sections from parse_node
       to focus fixes on the weakest areas.

    Reads:  resume_text, ats_result, rag_*_context
    Writes: state["critical_fixes_result"]
    """
    print("🔧 Critical Fixes Node: Generating URGENT fixes (score was < 50)...")
    result = run_critical_fixes_agent(
        resume_text=state["resume_text"],
        ats_result=state.get("ats_result", {}),
        rag_skills_context=state.get("rag_skills_context", ""),
        rag_experience_context=state.get("rag_experience_context", ""),
        rag_education_context=state.get("rag_education_context", "")
    )
    return {"critical_fixes_result": result}


def suggestions_node(state: ResumeState) -> dict:
    """
    Node 3b: Suggestions

    📌 ALWAYS RUNS:
       - If ATS score < 50: runs AFTER critical_fixes_node
       - If ATS score >= 50: runs DIRECTLY after ats_node
       Either way, suggestions are always generated.

    Reads:  state["resume_text"], state["ats_result"]
    Writes: state["suggestions_result"]
    """
    print("💡 Suggestions Node: Generating improvement tips...")
    ats_score = state.get("ats_result", {}).get("overall_score", 50)
    result = run_suggestions_agent(state["resume_text"], ats_score)
    return {"suggestions_result": result}


def web_research_node(state: ResumeState) -> dict:
    """
    Node 4: Web Research (v2.0 NEW — Uses Prebuilt Tools)

    📌 PREBUILT TOOLS USED:
       - DuckDuckGo → free web search (no API key!)
       - Tavily     → AI-optimized search (free tier)
       - Wikipedia  → knowledge lookup (free)

       These are imported from utils/tools.py and called
       inside the web_research_agent.

    📌 WHAT IT SEARCHES FOR:
       - Trending skills for the detected role
       - Salary range for the role
       - Industry overview from Wikipedia

    Reads:  state["keyword_result"] (needs detected_role + found_keywords)
    Writes: state["web_research_result"]
    """
    print("🌐 Web Research Node: Searching the internet for market data...")
    keyword_data = state.get("keyword_result", {})
    detected_role = keyword_data.get("detected_role", "Software Engineer")
    found_keywords = keyword_data.get("found_keywords", [])

    result = run_web_research_agent(detected_role, found_keywords)
    return {"web_research_result": result}


def job_search_node(state: ResumeState) -> dict:
    """
    Node 5: Job Search (v2.0 NEW — Uses JSearch API)

    📌 WHAT IS JSEARCH?
       A RapidAPI service that aggregates real job listings
       from LinkedIn, Indeed, Glassdoor, and other boards.
       Free tier: 200 requests/month.

    📌 WHAT IT RETURNS:
       Real job listings with:
       - Job title, company, location
       - Apply link (actual URL!)
       - AI analysis of how well the candidate fits

    Reads:  state["keyword_result"] (needs detected_role + found_keywords)
    Writes: state["job_search_result"]
    """
    print("💼 Job Search Node: Finding real matching jobs...")
    keyword_data = state.get("keyword_result", {})
    detected_role = keyword_data.get("detected_role", "Software Engineer")
    found_keywords = keyword_data.get("found_keywords", [])

    result = run_job_search_agent(detected_role, found_keywords)
    return {"job_search_result": result}


def aggregator_node(state: ResumeState) -> dict:
    """
    Node 6: Aggregator (v2.0 ENHANCED)

    📌 FAN-IN / JOIN:
       This node has TWO incoming edges:
       - From suggestions_node (Branch 1: ATS path)
       - From job_search_node (Branch 2: Keyword path)

       LangGraph WAITS for BOTH branches to complete
       before running this node. This is the "join" point
       where the parallel branches converge.

    📌 WHAT IT DOES:
       Combines ALL results from ALL agents into one
       clean response dict that gets sent to the frontend.

    Reads:  ALL state fields
    Writes: state["final_result"]
    """
    print("✅ Aggregator Node: Combining all results from both branches...")

    final = {
        # ── Core Analysis (from v1.0) ──────────────────────
        "ats":             state.get("ats_result", {}),
        "keywords":        state.get("keyword_result", {}),
        "suggestions":     state.get("suggestions_result", {}),

        # ── New Features (v2.0) ────────────────────────────
        "critical_fixes":  state.get("critical_fixes_result"),     # None if score >= 50
        "web_research":    state.get("web_research_result", {}),
        "job_search":      state.get("job_search_result", {}),

        # ── Pipeline Metadata ──────────────────────────────
        "pipeline_version": "2.0",
        "features_used": {
            "rag":                   True,
            "parallel_execution":    True,
            "conditional_branching": state.get("critical_fixes_result") is not None,
            "web_search":            True,
            "job_search":            bool((state.get("job_search_result") or {}).get("job_listings")),
        }
    }

    return {"final_result": final}


# ═════════════════════════════════════════════
#  STEP 3: CONDITIONAL ROUTER
#
#  📌 WHAT IS A CONDITIONAL EDGE?
#     In v1.0, every node always led to the next one.
#     In v2.0, we can CHOOSE which node to go to next
#     based on the current state!
#
#     It's like an IF statement in your graph:
#       if score < 50 → go to critical_fixes_node
#       else          → go to suggestions_node
#
#  📌 HOW IT WORKS:
#     1. The router function receives the current state
#     2. It checks the ATS score
#     3. It returns the NAME of the next node to run
#     4. LangGraph uses this name to route the flow
# ═════════════════════════════════════════════

def route_after_ats(state: ResumeState) -> str:
    """
    Conditional router: decides what happens after ATS analysis.

    Returns:
        "critical_fixes_node" → if ATS score < 50 (urgent!)
        "suggestions_node"    → if ATS score >= 50 (normal)
    """
    score = state.get("ats_result", {}).get("overall_score", 50)

    if score < ATS_CRITICAL_THRESHOLD:
        print(f"   ⚠️ ATS Score {score} < {ATS_CRITICAL_THRESHOLD} → Routing to CRITICAL FIXES")
        return "critical_fixes_node"
    else:
        print(f"   ✅ ATS Score {score} >= {ATS_CRITICAL_THRESHOLD} → Normal flow (skip fixes)")
        return "suggestions_node"


# ═════════════════════════════════════════════
#  STEP 4: BUILD THE GRAPH
#
#  📌 THIS IS THE v2.0 SMART GRAPH
#     The most important part of the file!
#
#     VISUAL REPRESENTATION:
#
#                      ┌──→ [ats_node] ──→ {score<50?} ──→ [critical_fixes] ──→ [suggestions] ──┐
#     [parse_node] ────┤                          │ ≥50                                          ├──→ [aggregator] → END
#                      │                          └────────────────────→ [suggestions] ──────────┘
#                      └──→ [keyword_node] ──→ [web_research] ──→ [job_search] ─────────────────┘
#
#     BRANCH 1 (top):    ATS scoring → [maybe critical fixes] → suggestions
#     BRANCH 2 (bottom): Keywords → web research → real job search
#     MERGE:             Both branches → aggregator → END
# ═════════════════════════════════════════════

def build_resume_graph():
    """
    Builds and compiles the enhanced v2.0 LangGraph workflow.

    v2.0 Features:
    - Parallel fan-out    : parse_node → ats + keyword simultaneously
    - Conditional edges   : ats → critical_fixes OR suggestions
    - Fan-in / join       : suggestions + job_search → aggregator
    - RAG context         : parse_node pre-queries sections

    Returns:
        A compiled graph that can be invoked like a function.
    """

    # ── Create the graph builder with our expanded state ────
    builder = StateGraph(ResumeState)

    # ── Add ALL nodes (8 total — up from 4 in v1.0) ────────
    builder.add_node("parse_node",          parse_node)          # NEW: RAG indexing
    builder.add_node("ats_node",            ats_node)            # Existing
    builder.add_node("keyword_node",        keyword_node)        # Enhanced with RAG
    builder.add_node("critical_fixes_node", critical_fixes_node) # NEW: conditional
    builder.add_node("suggestions_node",    suggestions_node)    # Existing
    builder.add_node("web_research_node",   web_research_node)   # NEW: web tools
    builder.add_node("job_search_node",     job_search_node)     # NEW: JSearch API
    builder.add_node("aggregator_node",     aggregator_node)     # Enhanced

    # ── ENTRY POINT ─────────────────────────────────────────
    # 📌 Everything starts at parse_node (RAG indexing)
    builder.set_entry_point("parse_node")

    # ── PARALLEL FAN-OUT ────────────────────────────────────
    #
    # 📌 MAGIC OF PARALLELISM:
    #    By adding TWO edges from parse_node, LangGraph
    #    runs both target nodes SIMULTANEOUSLY!
    #    This is like having two workers on an assembly line
    #    working on different tasks at the same time.
    #
    builder.add_edge("parse_node", "ats_node")       # Branch 1 starts
    builder.add_edge("parse_node", "keyword_node")   # Branch 2 starts
    #                                                  (both run in parallel!)

    # ── BRANCH 1: ATS Path (with conditional routing) ──────
    #
    # 📌 CONDITIONAL EDGE:
    #    Instead of add_edge() (always goes to one place),
    #    add_conditional_edges() calls a ROUTER FUNCTION
    #    that decides where to go based on the state.
    #
    #    route_after_ats() checks the ATS score and returns
    #    either "critical_fixes_node" or "suggestions_node"
    #
    builder.add_conditional_edges(
        "ats_node",              # Source node
        route_after_ats,         # Router function
        {                        # Possible destinations:
            "critical_fixes_node": "critical_fixes_node",  # score < 50
            "suggestions_node":    "suggestions_node"      # score >= 50
        }
    )
    # After critical fixes, ALWAYS go to suggestions
    builder.add_edge("critical_fixes_node", "suggestions_node")
    # After suggestions, go to aggregator
    builder.add_edge("suggestions_node", "aggregator_node")

    # ── BRANCH 2: Keyword Path (with web + job search) ─────
    #
    # 📌 This is a sequential chain within Branch 2:
    #    keyword_node → web_research → job_search → aggregator
    #    Each node uses data from the previous one.
    #
    builder.add_edge("keyword_node",      "web_research_node")
    builder.add_edge("web_research_node", "job_search_node")
    builder.add_edge("job_search_node",   "aggregator_node")

    # ── FAN-IN / JOIN at aggregator ─────────────────────────
    #
    # 📌 aggregator_node has TWO incoming edges:
    #    - From suggestions_node (Branch 1)
    #    - From job_search_node (Branch 2)
    #
    #    LangGraph automatically WAITS for BOTH to complete
    #    before running aggregator_node. This is the "join".
    #
    builder.add_edge("aggregator_node", END)

    # ── COMPILE the graph ──────────────────────────────────
    #
    # 📌 compile() does several things:
    #    1. Validates all edges (no orphan nodes, no cycles)
    #    2. Determines execution order
    #    3. Identifies parallel branches
    #    4. Returns a runnable graph object
    #
    graph = builder.compile()
    print("📊 LangGraph v2.0 compiled successfully!")

    return graph


# ═════════════════════════════════════════════
#  STEP 5: MAIN FUNCTION TO RUN THE GRAPH
# ═════════════════════════════════════════════

def run_resume_analysis(resume_text: str) -> dict:
    """
    Main entry point: runs the full v2.0 resume analysis pipeline.

    📌 v2.0 Enhancements:
       - RAG-powered section extraction
       - Parallel ATS + Keyword analysis
       - Conditional critical fixes (if score < 50)
       - Web research (trending skills, salary, Wikipedia)
       - Real job listings (JSearch API)
       - Fan-in aggregation of all results

    Args:
        resume_text : Plain text extracted from resume

    Returns:
        A dict with ALL analysis results:
        {
            "ats": {...},
            "keywords": {...},
            "suggestions": {...},
            "critical_fixes": {...} or None,
            "web_research": {...},
            "job_search": {...},
            "pipeline_version": "2.0",
            "features_used": {...}
        }
    """

    print("\n" + "=" * 60)
    print("  🚀 ResumeAI v2.0 Pipeline Starting...")
    print("  Features: RAG | Parallel | Conditional | Web Search | Jobs")
    print("=" * 60 + "\n")

    # Build the graph (compiled, ready to run)
    graph = build_resume_graph()

    # Initialize state — all Optional fields start as None
    initial_state = {
        "resume_text":             resume_text,

        # RAG context (filled by parse_node)
        "rag_skills_context":      None,
        "rag_experience_context":  None,
        "rag_education_context":   None,

        # Agent results (filled by respective nodes)
        "ats_result":              None,
        "keyword_result":          None,
        "suggestions_result":      None,
        "critical_fixes_result":   None,
        "web_research_result":     None,
        "job_search_result":       None,

        # Final output (filled by aggregator_node)
        "final_result":            None,
    }

    # ── Run the graph! ──────────────────────────────────────
    # 📌 invoke() executes the entire graph from start to end.
    #    It handles:
    #    - Parallel execution of independent nodes
    #    - Conditional routing based on state
    #    - Waiting for all branches at fan-in points
    #    - State merging from parallel branches
    #
    final_state = graph.invoke(initial_state)

    print("\n" + "=" * 60)
    print("  ✅ ResumeAI v2.0 Pipeline Complete!")
    print("=" * 60 + "\n")

    return final_state.get("final_result", {})
