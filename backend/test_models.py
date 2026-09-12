from langchain_google_genai import ChatGoogleGenerativeAI
from config import GOOGLE_API_KEY
import sys
sys.stdout.reconfigure(encoding='utf-8')

# The new model listed in the 2026 documentation the user provided!
models = ['gemini-3.8-flash']

print("Testing Gemini 3.8 Flash...")
for m in models:
    try:
        llm = ChatGoogleGenerativeAI(model=m, google_api_key=GOOGLE_API_KEY)
        res = llm.invoke('hi')
        print(f"✅ {m} OK")
    except Exception as e:
        print(f"❌ {m} FAILED: {str(e)}")
