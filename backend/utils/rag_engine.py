"""
============================================================
  utils/rag_engine.py  —  RAG (Retrieval Augmented Generation) Engine

  📌 WHAT IS RAG?
     RAG = Retrieval Augmented Generation
     Instead of sending the ENTIRE document to the AI,
     we first SPLIT it into small pieces, SEARCH for the
     most relevant pieces, then send ONLY those to the AI.

     Think of it like a library:
     - Without RAG: You read EVERY book to answer a question
     - With RAG:    You search the index, find the RIGHT chapter,
                    then read only that chapter

  📌 HOW DOES RAG WORK? (5 Steps)
     ┌─────────────────────────────────────────────────┐
     │  1. LOAD      → Get the document text           │
     │  2. SPLIT     → Break into small chunks         │
     │  3. EMBED     → Convert chunks to number vectors│
     │  4. STORE     → Save vectors in a vector store  │
     │  5. QUERY     → Find similar chunks by question │
     └─────────────────────────────────────────────────┘

  📌 WHAT IS FAISS?
     FAISS (Facebook AI Similarity Search) is a vector
     database that runs LOCALLY on your machine.
     No cloud service needed! It stores the embeddings
     and finds the most similar ones when you query.

  📌 WHAT ARE EMBEDDINGS?
     Embeddings convert text into a list of numbers
     (a "vector") that captures the MEANING of the text.
     Similar texts have similar vectors.
     Example:
       "Python programming" → [0.23, 0.87, 0.12, ...]
       "coding in Python"   → [0.25, 0.85, 0.14, ...]  ← very similar!
       "cooking pasta"      → [0.91, 0.03, 0.77, ...]  ← very different!

  📌 WHAT IS RecursiveCharacterTextSplitter?
     The BEST text splitter in LangChain. It tries to keep
     meaningful units together by splitting in this order:
       1. First try splitting by paragraphs (\n\n)
       2. If still too big, split by sentences (\n)
       3. If still too big, split by words
       4. Last resort: split by characters
     This prevents cutting sentences in half!
============================================================
"""

from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from config import GOOGLE_API_KEY, RAG_CHUNK_SIZE, RAG_CHUNK_OVERLAP


from langchain_huggingface import HuggingFaceEmbeddings

class ResumeRAGEngine:
    """
    📌 WHAT IS THIS CLASS?
       A complete RAG pipeline for resume analysis.
       It takes resume text, splits it into chunks,
       creates embeddings, stores in FAISS, and lets
       you query for specific sections.

       Usage:
         rag = ResumeRAGEngine("John Doe, Python developer...")
         skills = rag.query("What are the candidate's technical skills?")
         experience = rag.get_section("work experience")
    """

    def __init__(self, resume_text: str):
        """
        Initializes the RAG pipeline:
        1. Creates a LangChain Document from the resume text
        2. Splits it into overlapping chunks
        3. Generates embeddings using Google's embedding model
        4. Stores everything in a local FAISS vector store

        Args:
            resume_text : The full plain text of the resume
        """
        self.resume_text = resume_text

        # ── STEP 1: Create a LangChain Document ──────────────
        #
        # 📌 Document is LangChain's standard format for text data.
        #    It has two parts:
        #    - page_content : the actual text
        #    - metadata     : extra info (source, page number, etc.)
        #
        doc = Document(
            page_content=resume_text,
            metadata={"source": "uploaded_resume"}
        )

        # ── STEP 2: Split into chunks ────────────────────────
        #
        # 📌 WHY SPLIT?
        #    LLMs have token limits. Even if the resume fits,
        #    sending LESS text = more focused analysis.
        #
        # 📌 RecursiveCharacterTextSplitter is the BEST splitter:
        #    - chunk_size=500    → each chunk is ~500 characters
        #    - chunk_overlap=100 → neighboring chunks share 100 chars
        #                          (prevents cutting mid-sentence)
        #    - separators        → tries paragraph first, then sentence, etc.
        #
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=RAG_CHUNK_SIZE,
            chunk_overlap=RAG_CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", ", ", " ", ""]
            #           ↑↑↑     ↑↑    ↑↑    ↑↑   ↑    ↑
            #       paragraph sentence period comma word char
            #       (tries these in order, uses the first that works)
        )
        self.chunks = splitter.split_documents([doc])
        print(f"   📄 RAG: Split resume into {len(self.chunks)} chunks")

        # ── STEP 3 & 4: Embed + Store in FAISS ──────────────
        #
        # 📌 We are now using HuggingFace's "all-MiniLM-L6-v2" model!
        #    This is 100% FREE, runs locally on your machine, and
        #    does not use any Google API quota!
        self.embeddings = HuggingFaceEmbeddings(
            model_name="all-MiniLM-L6-v2"
        )

        self.vector_store = FAISS.from_documents(
            documents=self.chunks,
            embedding=self.embeddings
        )
        print(f"   🧠 RAG: Vector store created with {len(self.chunks)} embeddings")


    def query(self, question: str, k: int = 3) -> str:
        """
        📌 SEMANTIC SEARCH — the magic of RAG!

           Finds the k most relevant chunks for your question.
           Unlike keyword search ("find word X"), semantic search
           understands MEANING:

           query: "programming skills"
           finds: "Proficient in Python, Java, and React"
           (even though "programming skills" isn't in that text!)

           HOW IT WORKS:
           1. Convert your question into an embedding vector
           2. Find chunks whose vectors are CLOSEST to your question
              (using cosine similarity — a math measure of angle between vectors)
           3. Return those chunks as text

        Args:
            question : What you're looking for (natural language)
            k        : How many chunks to return (default 3)

        Returns:
            Combined text of the most relevant chunks
        """
        # similarity_search finds chunks whose embeddings are
        # closest to the question's embedding (cosine similarity)
        docs = self.vector_store.similarity_search(question, k=k)

        # Combine the matching chunks into one string
        combined = "\n\n".join([doc.page_content for doc in docs])
        return combined


    def get_section(self, section_name: str) -> str:
        """
        Convenience method: queries for a specific resume section.

        Examples:
            rag.get_section("skills")       → finds skills section
            rag.get_section("experience")   → finds work experience
            rag.get_section("education")    → finds education section

        Args:
            section_name : Name of the section to find

        Returns:
            Text content of the most relevant chunks
        """
        return self.query(
            f"resume section about {section_name}, qualifications, details",
            k=2  # Sections are usually compact, 2 chunks is enough
        )
