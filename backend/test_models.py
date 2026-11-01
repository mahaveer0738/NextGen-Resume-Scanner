import sys
import os
sys.stdout.reconfigure(encoding='utf-8')

from config import GOOGLE_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL

print(f"--- Config Models ---")
print(f"GROQ_MODEL: {GROQ_MODEL}")
print(f"GEMINI_MODEL: {GEMINI_MODEL}")
print(f"GROQ_API_KEY set: {bool(GROQ_API_KEY)} (prefix: {GROQ_API_KEY[:8] if GROQ_API_KEY else 'none'})")
print(f"GOOGLE_API_KEY set: {bool(GOOGLE_API_KEY)} (prefix: {GOOGLE_API_KEY[:8] if GOOGLE_API_KEY else 'none'})")

# 1. Test Groq
print("\nTesting Groq model...")
try:
    from langchain_groq import ChatGroq
    llm_groq = ChatGroq(model=GROQ_MODEL, groq_api_key=GROQ_API_KEY, request_timeout=10, max_retries=1)
    res = llm_groq.invoke("Say 'Groq is working' in 3 words")
    print(f"✅ Groq SUCCESS: {res.content.strip()}")
except Exception as e:
    print(f"❌ Groq ERROR: {e}")

# 2. Test Gemini
print("\nTesting Gemini model...")
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
    llm_gemini = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GOOGLE_API_KEY, request_timeout=10, max_retries=1)
    res = llm_gemini.invoke("Say 'Gemini is working' in 3 words")
    print(f"✅ Gemini SUCCESS: {res.content.strip()}")
except Exception as e:
    print(f"❌ Gemini ERROR: {e}")
