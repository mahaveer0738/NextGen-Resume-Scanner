"""
============================================================
  utils/helpers.py  —  Shared Utility Functions

  📌 WHAT IS A UTILS FILE?
     A place for small, reusable helper functions that
     are used by MULTIPLE files across the project.
     Instead of copy-pasting the same code everywhere,
     we write it once here and import it wherever needed.
============================================================
"""

import json
import re


def safe_parse_json(raw_text: str, fallback: dict = None) -> dict:
    """
    Safely parses JSON from LLM responses.
    LLMs sometimes wrap JSON in ```json code blocks.
    This function handles that gracefully.

    Args:
        raw_text : Raw string response from the LLM
        fallback : What to return if parsing fails

    Returns:
        Parsed dict or fallback dict
    """
    if fallback is None:
        fallback = {}

    # Remove markdown code fences like ```json ... ```
    cleaned = re.sub(r"```(?:json)?", "", raw_text).strip().strip("`").strip()

    try:
        return json.loads(cleaned)
    except (json.JSONDecodeError, ValueError):
        return fallback


def get_score_label(score: int) -> str:
    """
    Converts a numeric score to a human-readable label.

    Examples:
        85 → "Excellent"
        65 → "Good"
        45 → "Average"
        20 → "Needs Work"
    """
    if score >= 80:
        return "Excellent"
    elif score >= 65:
        return "Good"
    elif score >= 45:
        return "Average"
    else:
        return "Needs Work"


def truncate_text(text: str, max_chars: int = 8000) -> str:
    """
    Truncates very long resume text to avoid exceeding LLM token limits.
    Most resumes are under 3000 characters, but just in case.
    """
    if len(text) > max_chars:
        return text[:max_chars] + "\n... [text truncated for analysis]"
    return text
