from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from config import GOOGLE_API_KEY
import sys
sys.stdout.reconfigure(encoding='utf-8')

llm = ChatGoogleGenerativeAI(model="gemini-3.8-flash", google_api_key=GOOGLE_API_KEY)
response = llm.invoke([HumanMessage(content="Reply with exactly: {\"ok\": true}")])
print(type(response.content))
print(repr(response.content))
