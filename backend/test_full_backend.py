import os
import sys

# Add backend directory to sys.path so it can find local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from graph.resume_graph import run_resume_analysis
import json

sample_resume = """
Mahaveer Singh
Email: mahaveer@example.com
Phone: +91 9999999999

OBJECTIVE:
Software Engineer with 4 years of experience building scalable web applications.

SKILLS:
Python, Django, React, JavaScript, AWS, SQL, Machine Learning, TensorFlow

EXPERIENCE:
Software Engineer - Tech Corp (2020 - 2024)
- Built microservices using Python and FastAPI.
- Deployed applications to AWS.
- Implemented machine learning models using TensorFlow.

EDUCATION:
B.Tech in Computer Science - University of Technology
"""

print("Starting full backend LangGraph test...")
try:
    result = run_resume_analysis(sample_resume)
    print("\nTEST SUCCESSFUL! Final Output:")
    print(json.dumps(result, indent=2))
except Exception as e:
    print(f"\nTEST FAILED with error:")
    print(e)
    import traceback
    traceback.print_exc()
