# ================================================================
#  LEARN_AGENTS.py  -  Complete Guide: Tools, Agents, Executors
#
#  READ THIS FILE to understand HOW our AI agents work.
#  This is NOT a file that runs in production - it is a
#  LEARNING FILE with working examples you can test yourself.
#
#  Run this file:
#      .\venv\Scripts\python.exe LEARN_AGENTS.py
# ================================================================


# ================================================================
#  PART 1: WHAT IS A TOOL?
# ================================================================
#
#  A TOOL is just a Python function that:
#  1. Has a clear name
#  2. Has a docstring (the AI reads this to understand what it does)
#  3. Is wrapped with @tool decorator
#
#  The AI agent uses the DOCSTRING to decide WHEN to call the tool.
#  So the docstring is very important — it's the tool's "menu description".
#
# ================================================================

from langchain.tools import tool

# ── EXAMPLE 1: Simple Custom Tool ────────────────────────────────

@tool
def calculate_ats_score(resume_text: str) -> str:
    """
    Calculates the ATS (Applicant Tracking System) score for a resume.
    Use this when you need to evaluate how ATS-friendly a resume is.
    Input should be the plain text content of the resume.
    """
    # This is where your actual logic goes
    word_count = len(resume_text.split())
    has_email = "@" in resume_text
    has_phone = any(char.isdigit() for char in resume_text)

    score = 50
    if word_count > 200: score += 20
    if has_email: score += 15
    if has_phone: score += 15

    return f"ATS Score: {score}/100. Word count: {word_count}"


@tool
def extract_keywords(resume_text: str) -> str:
    """
    Extracts important technical skills and keywords from a resume.
    Use this when you need to find what skills a candidate has.
    Input should be the plain text of the resume.
    """
    # In real code, you'd use AI here — simplified for learning
    common_skills = ["Python", "Java", "React", "SQL", "AWS",
                     "Machine Learning", "Docker", "Git"]
    found = [skill for skill in common_skills if skill.lower() in resume_text.lower()]
    return f"Found keywords: {', '.join(found)}"


@tool
def search_jobs(job_title: str) -> str:
    """
    Searches for current job listings for a given job title.
    Use this when you need to find relevant job openings.
    Input should be a job title like 'Python Developer' or 'Data Scientist'.
    """
    # In real code you'd call Tavily or JSearch API here
    return f"Found 15 job listings for '{job_title}' on LinkedIn and Indeed."


# ── KEY POINT ──────────────────────────────────────────────────
# Notice: The @tool decorator does 3 things automatically:
# 1. Converts the function into a LangChain Tool object
# 2. Uses the function NAME as the tool's name
# 3. Uses the DOCSTRING as the tool's description (AI reads this!)

print("Tools defined:")
print(f"  Tool 1: {calculate_ats_score.name}")
print(f"  Tool 2: {extract_keywords.name}")
print(f"  Tool 3: {search_jobs.name}")
print()


# ================================================================
#  PART 2: OLD WAY — Agent + AgentExecutor (LangChain < 0.2)
#
#  You mentioned this pattern — let me show you EXACTLY how it works
#  and then show the BETTER modern way.
# ================================================================

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain_core.prompts import ChatPromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

# ── STEP 1: Create the LLM ───────────────────────────────────────
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    google_api_key=os.getenv("GOOGLE_API_KEY"),
    temperature=0
)

# ── STEP 2: Collect all Tools ────────────────────────────────────
tools = [calculate_ats_score, extract_keywords, search_jobs]

# ── STEP 3: Create a Prompt Template ────────────────────────────
# This is the "system instructions" for the agent
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful resume analysis assistant.
    You have access to tools. Use them to help users analyze their resumes.
    Always use tools to get accurate information."""),
    ("human", "{input}"),
    ("placeholder", "{agent_scratchpad}"),  # ← Where the agent "thinks"
])

# ── STEP 4: Create the AGENT ─────────────────────────────────────
#
# 📌 WHAT IS AN AGENT?
#    Agent = LLM + Tools + Reasoning Logic
#
#    The agent is the "brain" that:
#    - Reads the user's request
#    - THINKS about what tools to use
#    - Decides the ORDER to call tools
#    - Reads tool results and decides next action
#
agent = create_tool_calling_agent(llm, tools, prompt)

# ── STEP 5: Create the AGENT EXECUTOR ───────────────────────────
#
# 📌 WHAT IS AN AGENT EXECUTOR?
#    AgentExecutor = The LOOP that runs the agent repeatedly
#    until the agent says "I'm done"
#
#    Think of it this way:
#    - Agent = a chess player who decides moves
#    - AgentExecutor = the person who says "keep playing until checkmate"
#
#    The loop works like this:
#    ┌─────────────────────────────────────────────────┐
#    │  1. Agent reads user question                   │
#    │  2. Agent decides: "I need to call tool X"      │
#    │  3. Executor calls tool X                       │
#    │  4. Executor gives result back to agent         │
#    │  5. Agent thinks again...                       │
#    │  6. Agent decides: "Call tool Y now"            │
#    │  7. Executor calls tool Y                       │
#    │  8. Agent thinks: "I have enough info, done!"   │
#    │  9. Executor returns final answer               │
#    └─────────────────────────────────────────────────┘
#
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,        # Shows the agent's "thinking" steps
    max_iterations=5,    # Stop after 5 tool calls (prevents infinite loops)
    handle_parsing_errors=True
)

# ── HOW TO USE IT ────────────────────────────────────────────────
#
# result = agent_executor.invoke({
#     "input": "Analyze this resume: John Doe, Python developer, john@email.com"
# })
# print(result["output"])
#
# The agent will AUTOMATICALLY decide to call:
# → calculate_ats_score()  first
# → extract_keywords()     second
# → Then give a final answer combining both results


# ================================================================
#  PART 3: NEW WAY — LangGraph (What WE are using — BETTER!)
#
#  📌 WHY IS LANGGRAPH BETTER THAN AGENTEXECUTOR?
#
#  AgentExecutor problem:
#  - Single agent loop — hard to control
#  - Can't have multiple specialized agents easily
#  - No clear state management
#  - Hard to add conditional logic ("if score < 50, run improvement agent")
#
#  LangGraph solution:
#  - Multiple agents, each expert at ONE thing (nodes)
#  - Clear state flows between agents (edges)
#  - Conditional branching ("if X then go to agent A, else go to agent B")
#  - Full control over the workflow
#
# ================================================================

from langgraph.graph import StateGraph, END
from typing import TypedDict, Optional


# ── STEP 1: Define State ─────────────────────────────────────────
# State = the shared "notepad" all agents can read and write to

class ResumeState(TypedDict):
    resume_text:    str
    ats_score:      Optional[int]
    keywords:       Optional[list]
    final_answer:   Optional[str]


# ── STEP 2: Define Nodes (each node = one specialized agent) ─────

def ats_node(state: ResumeState) -> dict:
    """Agent 1: Only responsible for ATS scoring"""
    result = calculate_ats_score.invoke(state["resume_text"])
    score = int(result.split(":")[1].split("/")[0].strip())
    print(f"  ATS Node ran → Score: {score}")
    return {"ats_score": score}


def keyword_node(state: ResumeState) -> dict:
    """Agent 2: Only responsible for keyword extraction"""
    result = extract_keywords.invoke(state["resume_text"])
    keywords = result.replace("Found keywords: ", "").split(", ")
    print(f"  Keyword Node ran → Found: {keywords}")
    return {"keywords": keywords}


def summary_node(state: ResumeState) -> dict:
    """Agent 3: Combines results into a final answer"""
    score = state.get("ats_score", 0)
    keywords = state.get("keywords", [])
    summary = f"Resume Analysis Complete! ATS Score: {score}/100. Skills found: {', '.join(keywords)}"
    print(f"  Summary Node ran")
    return {"final_answer": summary}


# ── STEP 3: Build the Graph ──────────────────────────────────────

builder = StateGraph(ResumeState)

builder.add_node("ats_agent",     ats_node)
builder.add_node("keyword_agent", keyword_node)
builder.add_node("summary_agent", summary_node)

builder.set_entry_point("ats_agent")
builder.add_edge("ats_agent",     "keyword_agent")
builder.add_edge("keyword_agent", "summary_agent")
builder.add_edge("summary_agent", END)

graph = builder.compile()


# ── STEP 4: Run it! ──────────────────────────────────────────────

print("\n" + "="*60)
print("  RUNNING LANGGRAPH PIPELINE (local demo, no API call)")
print("="*60 + "\n")

sample_resume = """
John Doe | john@email.com | +91 9876543210
Python Developer with 3 years experience.
Skills: Python, React, SQL, Docker, Git, AWS
"""

result = graph.invoke({
    "resume_text":  sample_resume,
    "ats_score":    None,
    "keywords":     None,
    "final_answer": None
})

print(f"\n✅ FINAL RESULT: {result['final_answer']}")


# ================================================================
#  PART 4: SIDE-BY-SIDE COMPARISON
# ================================================================
#
#  OLD WAY (AgentExecutor):
#  ────────────────────────
#  agent = create_tool_calling_agent(llm, tools, prompt)
#  executor = AgentExecutor(agent=agent, tools=tools)
#  result = executor.invoke({"input": "analyze this resume..."})
#
#  ✅ Simple for small tasks
#  ❌ Single agent does everything — messy for complex tasks
#  ❌ Hard to control flow
#  ❌ Hard to add multiple specialized agents
#
#
#  NEW WAY (LangGraph) — What WE use:
#  ────────────────────────────────────
#  builder = StateGraph(State)
#  builder.add_node("ats",      ats_node)
#  builder.add_node("keywords", keyword_node)
#  builder.add_edge("ats", "keywords")
#  graph = builder.compile()
#  result = graph.invoke(initial_state)
#
#  ✅ Each agent has ONE job — clean and organized
#  ✅ Full control over the flow
#  ✅ Conditional branching possible
#  ✅ Professional production-grade pattern
#  ✅ What big companies (Google, Meta) use in production
#
# ================================================================

print("\n" + "="*60)
print("  SUMMARY")
print("="*60)
print("""
  @tool decorator  →  Wraps a Python function into an AI tool
  
  Agent            →  LLM + Tools + Reasoning
                      (the brain that decides what to do)
  
  AgentExecutor    →  The loop that keeps running the agent
                      until it says "I'm done"
                      (OLD way — simpler but less control)
  
  LangGraph Node   →  A specialized agent with ONE job
                      (NEW way — what we use)
  
  LangGraph Graph  →  Connects all nodes in a workflow
                      = AgentExecutor but MUCH more powerful
""")
