"""
============================================================
  agents/cover_letter_agent.py  —  Cover Letter Generator

  📌 WHAT DOES THIS AGENT DO?
     Takes the resume + target job title and generates a
     professional, personalized cover letter.

  📌 WHY IS THIS AN AGENT?
     Because it reads from the resume STATE (data that was
     already extracted earlier in the pipeline) and uses it
     to write something new. This is the "creative" agent.
============================================================
"""

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import GOOGLE_API_KEY, GEMINI_MODEL

llm = ChatGoogleGenerativeAI(
    model=GEMINI_MODEL,
    google_api_key=GOOGLE_API_KEY,
    temperature=0.7      # Higher creativity for writing tasks
)


def run_cover_letter_agent(resume_text: str, job_title: str, company_name: str = "") -> dict:
    """
    Generates a personalized cover letter.

    Args:
        resume_text  : Extracted resume text
        job_title    : Target job role (e.g., "Software Engineer")
        company_name : Optional company name

    Returns:
        dict with the generated cover letter text
    """

    company_line = f"at {company_name}" if company_name else ""

    prompt = f"""
You are a professional cover letter writer.
Write a compelling cover letter for a {job_title} position {company_line}.
Base it on the candidate's actual experience from their resume.

RESUME:
-------
{resume_text}
-------

Write a 3-4 paragraph professional cover letter that:
1. Opens with an engaging hook (not "I am applying for...")
2. Highlights 2-3 most relevant experiences from the resume
3. Shows enthusiasm for the role
4. Closes with a confident call to action

Respond ONLY with valid JSON:
{{
  "cover_letter": "<the full cover letter text with proper line breaks>",
  "word_count": <integer>
}}
"""

    response = llm.invoke([HumanMessage(content=prompt)])

    # Since this is text, we handle it more gently
    import re, json
    cleaned = re.sub(r"```(?:json)?", "", response.content).strip().strip("`").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        # If JSON parsing fails, just return the raw text
        return {
            "cover_letter": response.content.strip(),
            "word_count": len(response.content.split())
        }
