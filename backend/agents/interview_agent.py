"""
============================================================
  agents/interview_agent.py  —  Interview Questions Generator (Resilient)

  📌 WHAT DOES THIS AGENT DO?
     Reads the resume and target role, then generates
     tailored interview questions that a recruiter might ask
     THIS specific candidate based on their actual experience.
============================================================
"""

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import GOOGLE_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL
import json
import re


def run_interview_agent(resume_text: str, job_title: str) -> dict:
    """
    Generates tailored interview questions based on the resume.
    """

    prompt = f"""
You are an experienced interviewer for {job_title} positions.
Based on the resume below, generate interview questions this candidate might be asked.

RESUME:
-------
{resume_text[:3500]}
-------

Generate 9 interview questions in 3 categories (3 technical, 3 behavioral, 3 situational):
Respond ONLY with valid JSON:
{{
  "technical_questions": [
    {{"question": "<question>", "context_from_resume": "<context>", "suggested_answer_strategy": "<strategy>"}}
  ],
  "behavioral_questions": [
    {{"question": "<question>", "context_from_resume": "<context>", "suggested_answer_strategy": "<strategy>"}}
  ],
  "situational_questions": [
    {{"question": "<question>", "context_from_resume": "<context>", "suggested_answer_strategy": "<strategy>"}}
  ]
}}
"""

    response_content = None

    if GROQ_API_KEY and GROQ_MODEL:
        try:
            groq_llm = ChatGroq(model=GROQ_MODEL, groq_api_key=GROQ_API_KEY, temperature=0.3, request_timeout=15, max_retries=1)
            response = groq_llm.invoke([HumanMessage(content=prompt)])
            response_content = response.content
        except Exception as e:
            print(f"   ⚠️ Groq interview generation failed ({str(e)}), trying Gemini...")

    if not response_content and GOOGLE_API_KEY:
        try:
            gemini_llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GOOGLE_API_KEY, temperature=0.3, request_timeout=15, max_retries=1)
            response = gemini_llm.invoke([HumanMessage(content=prompt)])
            response_content = response.content
        except Exception as e:
            print(f"   ❌ Gemini interview generation failed: {str(e)}")

    if not response_content:
        return _fallback_interview(job_title)

    parsed = _parse_json_response(response_content)
    if not parsed.get("technical_questions"):
        return _fallback_interview(job_title)
    return parsed


def _fallback_interview(job_title: str) -> dict:
    return {
        "technical_questions": [
            {
                "question": f"Can you explain your approach to designing scalable RESTful APIs in a {job_title} role?",
                "context_from_resume": "Core engineering and backend development skills",
                "suggested_answer_strategy": "Discuss database design, indexing, caching, and rate limiting."
            },
            {
                "question": "How do you handle unit and integration testing before deploying to production?",
                "context_from_resume": "Quality assurance and testing workflows",
                "suggested_answer_strategy": "Mention automated CI/CD pipelines, test coverage, and staging environments."
            },
            {
                "question": "Describe an instance where you optimized a slow query or bottleneck.",
                "context_from_resume": "Performance tuning",
                "suggested_answer_strategy": "Walk through profiling, identifying the hot path, and measurable speedup."
            }
        ],
        "behavioral_questions": [
            {
                "question": "Tell me about a time you had a technical disagreement with a team member. How did you resolve it?",
                "context_from_resume": "Collaboration & team dynamics",
                "suggested_answer_strategy": "Use STAR method: focus on data-driven discussion and constructive consensus."
            },
            {
                "question": "Describe a project with ambiguous requirements and how you moved it forward.",
                "context_from_resume": "Problem ownership",
                "suggested_answer_strategy": "Explain how you clarified scope with stakeholders and iterated in agile sprints."
            },
            {
                "question": "How do you stay up-to-date with rapid changes in modern tech stacks?",
                "context_from_resume": "Continuous learning",
                "suggested_answer_strategy": "Share open-source contributions, reading docs, and building side projects."
            }
        ],
        "situational_questions": [
            {
                "question": "If a critical production service went down on a weekend, what steps would you follow?",
                "context_from_resume": "Incident management",
                "suggested_answer_strategy": "Triage, rollback/hotfix, communicate with stakeholders, write post-mortem."
            },
            {
                "question": "How would you handle a tight deadline when code quality might be compromised?",
                "context_from_resume": "Balancing speed and technical debt",
                "suggested_answer_strategy": "Deliver MVP, document technical debt, and schedule refactoring in next sprint."
            },
            {
                "question": f"What would be your top priority in the first 30 days as a {job_title} here?",
                "context_from_resume": "Onboarding & impact",
                "suggested_answer_strategy": "Understand architecture, meet stakeholders, and submit a small first PR."
            }
        ]
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
