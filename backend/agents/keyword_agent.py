"""
============================================================
  agents/keyword_agent.py  —  Keyword Analysis Agent (v2.0 ENHANCED)

  📌 WHAT DOES THIS AGENT DO?
     Extracts all technical skills, soft skills, and
     job-specific keywords from the resume. Then compares
     them with what the detected job role typically requires.

     Returns:
     - ✅ Keywords FOUND in resume
     - ❌ Keywords MISSING (common for that role)
     - Match percentage
============================================================
"""

from langchain_groq import ChatGroq
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import GROQ_API_KEY, GROQ_MODEL, GOOGLE_API_KEY, GEMINI_MODEL
import json
import re


def run_keyword_agent(resume_text: str, skills_context: str = "") -> dict:
    """
    Analyzes keywords in the resume.
    Now accepts RAG skills context for focused analysis.
    """

    rag_section = ""
    if skills_context and skills_context != resume_text:
        rag_section = f"""

FOCUSED SKILLS SECTION (extracted by RAG — pay special attention to this):
------
{skills_context}
------
"""

    prompt = f"""
You are an expert resume keyword analyzer.
Read the resume below and identify the candidate's target job role.

RESUME:
-------
{resume_text[:4000]}
-------
{rag_section}
Your tasks:
1. Detect the most likely job role (e.g., "Software Engineer", "Data Scientist", "Marketing Manager")
2. List ALL technical and soft skills/keywords FOUND in the resume
3. List important keywords that are MISSING for that role (top 8-10 missing ones)
4. Calculate a match percentage

Respond ONLY with valid JSON in this exact format:
{{
  "detected_role": "<detected job role>",
  "found_keywords": ["keyword1", "keyword2", ...],
  "missing_keywords": ["keyword1", "keyword2", ...],
  "match_percent": <integer 0-100>,
  "total_keywords_found": <integer>
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
            print(f"   ⚠️ Groq keyword extraction failed ({str(e)}), falling back to Gemini...")

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
            print(f"   ❌ Gemini keyword fallback failed: {str(e)}")

    if not response_content:
        return _heuristic_keyword_extraction(resume_text)

    parsed = _parse_json_response(response_content)
    if not parsed.get("found_keywords"):
        return _heuristic_keyword_extraction(resume_text)
    return parsed


def _heuristic_keyword_extraction(text: str) -> dict:
    """Fallback: extracts common technical keywords using regex dictionaries."""
    lower = text.lower()
    common_skills = [
        "Python", "JavaScript", "TypeScript", "React", "Node.js", "SQL", "PostgreSQL",
        "MongoDB", "HTML5", "CSS3", "Git", "GitHub", "Docker", "AWS", "FastAPI",
        "Django", "REST API", "Java", "C++", "Linux", "CI/CD", "Machine Learning",
        "Pandas", "NumPy", "Tailwind CSS", "Agile", "Scrum", "Kubernetes", "GraphQL"
    ]
    found = [skill for skill in common_skills if skill.lower() in lower]

    # Detect role
    if any(k in lower for k in ["data science", "machine learning", "pandas", "numpy"]):
        role = "Data Scientist / ML Engineer"
        missing = ["TensorFlow", "PyTorch", "MAPI", "Airflow", "Model Deployment", "MLOps"]
    elif any(k in lower for k in ["react", "javascript", "frontend", "css"]):
        role = "Frontend Developer"
        missing = ["Next.js", "Redux", "Webpack", "Performance Optimization", "Jest"]
    else:
        role = "Software Developer"
        missing = ["System Design", "Unit Testing", "Microservices", "Redis", "Kafka"]

    match_pct = min(95, max(40, len(found) * 8))

    return {
        "detected_role": role,
        "found_keywords": found if found else ["Communication", "Problem Solving", "Teamwork"],
        "missing_keywords": missing,
        "match_percent": match_pct,
        "total_keywords_found": len(found)
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
        return {
            "detected_role": "Candidate",
            "found_keywords": [],
            "missing_keywords": [],
            "match_percent": 0,
            "total_keywords_found": 0
        }
