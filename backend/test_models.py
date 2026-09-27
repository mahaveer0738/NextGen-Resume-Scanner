import sys
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from config import GOOGLE_API_KEY, GEMINI_MODEL, GROQ_API_KEY, GROQ_MODEL

sys.stdout.reconfigure(encoding='utf-8')

print(f"Testing Gemini Model: {GEMINI_MODEL}")
try:
    llm = ChatGoogleGenerativeAI(model=GEMINI_MODEL, google_api_key=GOOGLE_API_KEY)
    res = llm.invoke('hi')
    print(f"✅ {GEMINI_MODEL} OK")
except Exception as e:
    print(f"❌ {GEMINI_MODEL} FAILED: {str(e)}")

print(f"Testing Groq Model: {GROQ_MODEL}")
try:
    llm = ChatGroq(model=GROQ_MODEL, groq_api_key=GROQ_API_KEY)
    res = llm.invoke('hi')
    print(f"✅ {GROQ_MODEL} OK")
except Exception as e:
    print(f"❌ {GROQ_MODEL} FAILED: {str(e)}")
