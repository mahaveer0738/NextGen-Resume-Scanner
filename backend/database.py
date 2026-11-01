"""
============================================================
  database.py  —  SQLAlchemy Database Setup

  📌 WHAT IS THIS?
     Sets up a SQLite database using SQLAlchemy ORM.
     SQLite is a file-based database — no installation needed!
     The database file (resumeai.db) is created automatically
     in the backend/ directory when the app starts.

  📌 WHY SQLITE?
     - Zero configuration — just run and it works
     - Perfect for local development and small projects
     - No external database server needed
     - The .db file is portable
============================================================
"""

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# ─────────────────────────────────────────────
# DATABASE URL
# SQLite stores everything in a single file
# ─────────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_URL = f"sqlite:///{os.path.join(BASE_DIR, 'resumeai.db')}"

# ─────────────────────────────────────────────
# ENGINE
# The engine is the core of SQLAlchemy — it
# manages connections to the database.
# check_same_thread=False is needed for SQLite
# with FastAPI (multiple threads may share it)
# ─────────────────────────────────────────────
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# ─────────────────────────────────────────────
# SESSION FACTORY
# SessionLocal() creates a new database session
# for each request (like a conversation with the DB)
# ─────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ─────────────────────────────────────────────
# BASE CLASS
# All SQLAlchemy models inherit from this.
# ─────────────────────────────────────────────
Base = declarative_base()


# ─────────────────────────────────────────────
# DEPENDENCY: Get DB Session
# Used in FastAPI route functions via Depends()
# Automatically closes the session after request
# ─────────────────────────────────────────────
def get_db():
    """
    FastAPI dependency that yields a database session.

    Usage in a route:
        @router.get("/something")
        def my_route(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

