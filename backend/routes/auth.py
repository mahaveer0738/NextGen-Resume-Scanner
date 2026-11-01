"""
============================================================
  routes/auth.py  —  Authentication API Endpoints

  📌 ENDPOINTS:
     POST /api/auth/register  — Create a new account
     POST /api/auth/login     — Log in, get JWT token
     GET  /api/auth/me        — Get current user profile
     POST /api/auth/logout    — (Client-side token deletion)

  📌 HOW LOGIN WORKS:
     1. User sends { email, password }
     2. We verify the password against the stored bcrypt hash
     3. If correct, we issue a JWT access token
     4. Frontend stores the token in localStorage
     5. All subsequent API calls include: Authorization: Bearer <token>
============================================================
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional
from datetime import datetime

from database import get_db
import models
from utils.auth_utils import hash_password, verify_password, create_access_token, get_current_user

router = APIRouter()


# ─────────────────────────────────────────────
# PYDANTIC SCHEMAS (Request/Response models)
# ─────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username:  str
    email:     str
    full_name: Optional[str] = ""
    password:  str

    @field_validator("username")
    @classmethod
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError("Username must be at least 3 characters")
        if len(v) > 50:
            raise ValueError("Username must be at most 50 characters")
        if not v.replace("_", "").replace("-", "").isalnum():
            raise ValueError("Username can only contain letters, numbers, - and _")
        return v.lower()

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError("Password must be at least 6 characters")
        return v


class LoginRequest(BaseModel):
    email:    str
    password: str


class UserResponse(BaseModel):
    id:         int
    username:   str
    email:      str
    full_name:  Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type:   str = "bearer"
    user:         UserResponse


# ─────────────────────────────────────────────
# ENDPOINT: POST /api/auth/register
# ─────────────────────────────────────────────

@router.post("/auth/register", response_model=TokenResponse, status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user account.

    - Checks if email/username already taken
    - Hashes the password with bcrypt
    - Creates user in database
    - Returns a JWT token (user is immediately logged in)
    """

    # Check if email already exists
    existing_email = db.query(models.User).filter(models.User.email == request.email.lower()).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    # Check if username already taken
    existing_username = db.query(models.User).filter(models.User.username == request.username.lower()).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This username is already taken. Please choose another."
        )

    # Create new user
    new_user = models.User(
        username=request.username.lower(),
        email=request.email.lower(),
        full_name=request.full_name or "",
        hashed_password=hash_password(request.password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Generate JWT token
    token = create_access_token(data={"sub": str(new_user.id)})

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(new_user)
    )


# ─────────────────────────────────────────────
# ENDPOINT: POST /api/auth/login
# ─────────────────────────────────────────────

@router.post("/auth/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):
    """
    Log in with email + password.

    Returns a JWT token on success.
    Raises 401 if credentials are invalid.
    """

    # Find user by email
    user = db.query(models.User).filter(models.User.email == request.email.lower()).first()

    # Verify password
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate JWT token
    token = create_access_token(data={"sub": str(user.id)})

    return TokenResponse(
        access_token=token,
        user=UserResponse.model_validate(user)
    )


# ─────────────────────────────────────────────
# ENDPOINT: GET /api/auth/me
# Protected — requires valid JWT
# ─────────────────────────────────────────────

@router.get("/auth/me", response_model=UserResponse)
def get_me(current_user: models.User = Depends(get_current_user)):
    """
    Returns the profile of the currently logged-in user.
    Frontend calls this to check if the token is still valid.
    """
    return UserResponse.model_validate(current_user)

