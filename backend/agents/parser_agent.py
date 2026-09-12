"""
============================================================
  agents/parser_agent.py  —  PDF & DOCX Text Extractor

  📌 WHAT DOES THIS AGENT DO?
     Before any AI can analyze a resume, we need to EXTRACT
     the raw text from the uploaded file.
     - PDF files → use pdfplumber library
     - DOCX files → use python-docx library
     - After extraction → the text is passed to other agents

  📌 WHY A SEPARATE AGENT FOR PARSING?
     Separation of concerns — each agent has ONE job.
     The parser only reads files. The ATS agent only scores.
     This makes the code clean, testable, and reusable.
============================================================
"""

import pdfplumber
import docx
import io
from fastapi import HTTPException


# ─────────────────────────────────────────────
# MAIN FUNCTION: Extract text from uploaded file
# ─────────────────────────────────────────────

def extract_text_from_file(file_bytes: bytes, filename: str) -> str:
    """
    Takes the raw bytes of an uploaded file and returns clean text.

    Args:
        file_bytes : The raw binary content of the uploaded file
        filename   : Original filename (used to detect file type)

    Returns:
        A string with all the text from the resume
    """

    extension = filename.lower().split(".")[-1]

    if extension == "pdf":
        return _extract_from_pdf(file_bytes)

    elif extension in ("doc", "docx"):
        return _extract_from_docx(file_bytes)

    else:
        raise HTTPException(
            status_code=400,
            detail="Unsupported file type. Please upload PDF or DOCX."
        )


# ─────────────────────────────────────────────
# PRIVATE HELPER: Extract from PDF
# ─────────────────────────────────────────────

def _extract_from_pdf(file_bytes: bytes) -> str:
    """
    📌 pdfplumber reads PDF files page by page and extracts
       all the text. Much more accurate than PyPDF2 for resumes.
    """
    text_parts = []

    # Wrap bytes in a file-like object so pdfplumber can read it
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    full_text = "\n".join(text_parts).strip()

    if not full_text:
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from PDF. Make sure it's not a scanned image."
        )

    return full_text


# ─────────────────────────────────────────────
# PRIVATE HELPER: Extract from DOCX
# ─────────────────────────────────────────────

def _extract_from_docx(file_bytes: bytes) -> str:
    """
    📌 python-docx reads each paragraph in the Word document
       and joins them into one big string.
    """
    doc = docx.Document(io.BytesIO(file_bytes))

    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    full_text = "\n".join(paragraphs).strip()

    if not full_text:
        raise HTTPException(
            status_code=422,
            detail="Could not extract text from DOCX. The file appears to be empty."
        )

    return full_text
