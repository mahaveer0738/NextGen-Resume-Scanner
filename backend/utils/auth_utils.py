"""
============================================================
  utils/auth_utils.py  —  JWT Authentication Utilities

  📌 WHAT IS JWT?
     JSON Web Token — a compact, self-contained token
     that proves a user is logged in.

     Structure: header.payload.signature
     Example:   eyJhbGci....eyJ1c2VyX2lk....ABC123==

  📌 HOW DOES IT WORK?
     1. User logs in → server generates a JWT token
     2. Frontend stores the token (localStorage)
     3. Every API request sends: Authorization: Bearer <token>
     4. Server verifies the token → knows WHO is calling

  📌 WHY JWT (not sessions)?
     - Stateless — server doesn't need to store session data
     - Works great with REST APIs / SPAs
     - Portable — works across different domains
     - Industry standard for modern web apps

  📌 LIBRARIES USED:
     - python-jose[cryptography] — JWT creation/verification
     - passlib[bcrypt]           — secure password hashing
============================================================
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from database import get_db
import models
import os

# ─────────────────────────────────────────────
# CONFIGURATION
# ─────────────────────────────────────────────

# Secret key for signing JWTs — CHANGE THIS IN PRODUCTION!
# In production, set this as an environment variable
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "resumeai-super-secret-key-change-in-production-2024")

# Algorithm for JWT signing (HS256 = HMAC + SHA-256)
ALGORITHM = "HS256"

# Token expiry — 7 days (users stay logged in for a week)
ACCESS_TOKEN_EXPIRE_DAYS = 7


# ─────────────────────────────────────────────
# PASSWORD HASHING
# Direct bcrypt hashing handles passwords securely without passlib issues.
# NEVER store plain passwords — always hash them!
# ─────────────────────────────────────────────

def hash_password(plain_password: str) -> str:
    """
    Hash a plain password using bcrypt.
    Truncates to 72 bytes as required by bcrypt specification.
    """
    pwd_bytes = plain_password.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Check if a plain password matches a stored bcrypt hash.
    Used during login.
    """
    try:
        pwd_bytes = plain_password.encode('utf-8')[:72]
        return bcrypt.checkpw(pwd_bytes, hashed_password.encode('utf-8'))
    except Exception:
        return False


# ─────────────────────────────────────────────
# JWT TOKEN CREATION
# ─────────────────────────────────────────────

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Create a JWT access token.

    Args:
        data         : Payload to encode (usually {"sub": user_id})
        expires_delta: How long the token is valid (default: 7 days)

    Returns:
        A JWT string like "eyJhbGci..."
    """
    to_encode = data.copy()

    # Set expiry time
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS)

    to_encode.update({"exp": expire})

    # Create and sign the token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# ─────────────────────────────────────────────
# JWT TOKEN VERIFICATION
# ─────────────────────────────────────────────

def verify_token(token: str) -> Optional[int]:
    """
    Verify a JWT token and extract the user ID.

    Args:
        token : JWT string

    Returns:
        user_id (int) if valid, None if invalid/expired
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            return None
        return int(user_id)
    except JWTError:
        return None


# ─────────────────────────────────────────────
# FASTAPI SECURITY SCHEME
# HTTPBearer extracts the token from the
# "Authorization: Bearer <token>" header
# ─────────────────────────────────────────────
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> models.User:
    """
    FastAPI dependency: extracts and validates the JWT token,
    then returns the current logged-in User object.

    Usage in protected routes:
        @router.get("/protected")
        def protected_route(current_user: User = Depends(get_current_user)):
            return {"message": f"Hello, {current_user.username}!"}

    Raises:
        401 Unauthorized — if token is missing, invalid, or expired
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials. Please log in.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not credentials:
        raise credentials_exception

    token = credentials.credentials
    user_id = verify_token(token)

    if user_id is None:
        raise credentials_exception

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if user is None:
        raise credentials_exception

    return user


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> Optional[models.User]:
    """
    Like get_current_user but OPTIONAL — returns None if not logged in.
    Used for endpoints that work with or without authentication
    (e.g., /api/analyze — works for guests but saves history for logged-in users).
    """
    if not credentials:
        return None

    token = credentials.credentials
    user_id = verify_token(token)

    if user_id is None:
        return None

    return db.query(models.User).filter(models.User.id == user_id).first()

