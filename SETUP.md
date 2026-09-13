# 🛠️ NextGen Resume Scanner: Complete Setup Guide

This guide will walk you through the step-by-step process of setting up the **NextGen Resume Scanner (v2.0)** on your local machine.

## Prerequisites

Before you begin, ensure you have the following installed on your system:
- **Python 3.12+**
- **Git**

You will also need free API keys from the following providers:
- [Google AI Studio](https://aistudio.google.com/) (for Gemini 1.5 Flash)
- [Groq](https://console.groq.com/) (for Llama 3)
- [Tavily](https://tavily.com/) (Optional, but highly recommended for live market data)

---

## Step 1: Clone the Repository

Open your terminal or command prompt and run the following command to download the project:

```bash
git clone https://github.com/mahaveer0738/NextGen-Resume-Scanner.git
cd NextGen-Resume-Scanner
```

---

## Step 2: Set Up the Backend Environment

The backend is built with FastAPI and runs the Agentic Workflow. You need to create an isolated Python environment for it.

### 1. Navigate to the backend directory:
```bash
cd backend
```

### 2. Create a virtual environment:
```bash
python -m venv venv
```

### 3. Activate the virtual environment:
- **Windows (Command Prompt / PowerShell):**
  ```bash
  .\venv\Scripts\activate
  ```
- **Mac / Linux:**
  ```bash
  source venv/bin/activate
  ```

### 4. Install dependencies:
With the virtual environment activated, install all required Python packages:
```bash
pip install -r requirements.txt
```

---

## Step 3: Configure Environment Variables

The AI agents require API keys to function. 

1. Inside the `backend/` directory, create a new file named `.env`.
2. Open the `.env` file in your text editor and add your API keys in the following format:

```env
GOOGLE_API_KEY=your_gemini_key_here
GROQ_API_KEY=your_groq_key_here
TAVILY_API_KEY=your_tavily_key_here
```
*(Note: Do not put quotes around the keys. Just paste the raw keys.)*

---

## Step 4: Run the Backend Server

With your dependencies installed and environment variables set, you can start the backend server.

1. Ensure your virtual environment is still active.
2. Ensure you are in the `backend/` directory.
3. Run the following command:

```bash
python -m uvicorn main:app --port 8000
```

*If successful, you will see output indicating that Uvicorn is running on `http://127.0.0.1:8000`.*

> **Test the Backend:** You can visit [http://localhost:8000/docs](http://localhost:8000/docs) in your browser to view the interactive FastAPI Swagger UI and ensure the backend is running perfectly.

---

## Step 5: Launch the Frontend

The frontend of this project is incredibly lightweight and uses no frameworks like React or npm. It runs directly in your browser.

1. Open your computer's **File Explorer** (or Finder).
2. Navigate to the `NextGen-Resume-Scanner/frontend/` folder.
3. Double-click on the `index.html` file. 

This will open the application in your default web browser!

---

## Step 6: Test the System

1. With `index.html` open in your browser, and the `uvicorn` backend server running in your terminal, click on the **Upload Your Resume** button.
2. Select a PDF or DOCX file (under 5MB).
3. Watch the system invoke LangGraph, extract keywords, query the live internet, and evaluate your resume!

## Troubleshooting

- **"Connection Refused" Error on Frontend**: This means your backend server is not running. Go back to Step 4 and ensure the Uvicorn server is running on port 8000.
- **API Key Errors**: Ensure your `.env` file is located exactly inside the `backend/` directory and contains valid keys.
