"""
backend/app/api/endpoints/auth.py
──────────────────────────────────
Authentication Router exposing Login, Register, Profile, Refresh, and Logout.
"""

# from __future__ import annotations

from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status, Response, Request
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

from app.core.auth import (
    UserRole,
    create_access_token,
    create_refresh_token,
    get_current_user,
    get_password_hash,
    verify_password,
    jwt,
    settings,
    oauth2_scheme,
)
from app.core.database import get_db
from app.models.db_models import User, AuditLog
from app.core.logging import get_logger
from app.core.limiter import limiter

logger = get_logger(__name__)

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

# ── Pydantic Schemas ─────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50, examples=["operator2"])
    email: EmailStr = Field(..., examples=["operator2@nika.ai"])
    password: str = Field(..., min_length=6, examples=["supersecure123"])
    role: str = Field(default=UserRole.OPERATOR, examples=["operator", "supervisor", "viewer"])


class UserResponse(BaseModel):
    id: str
    username: str
    email: str
    role: str

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserResponse


class RefreshRequest(BaseModel):
    refresh_token: str


class LoginRequest(BaseModel):
    username: str = Field(..., examples=["admin1"])
    password: str = Field(..., examples=["admin123"])


# ── Routes ───────────────────────────────────────────────────────────────────

@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user account"
)
@limiter.limit("3/minute")
async def register(
    request: Request,
    user_in: UserRegister,
    db: Session = Depends(get_db)
) -> User:
    """Create a new user account with hashed password and role assignment."""
    # Check if user already exists
    existing_user = db.query(User).filter(
        (User.username == user_in.username) | (User.email == user_in.email)
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username or email is already registered."
        )

    # Validate role
    role = user_in.role.lower()
    allowed_roles = {UserRole.ADMIN, UserRole.SUPERVISOR, UserRole.OPERATOR, UserRole.VIEWER}
    if role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid role. Allowed roles are: {', '.join(allowed_roles)}"
        )

    hashed_pw = get_password_hash(user_in.password)
    new_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hashed_pw,
        role=role
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        logger.info(f"Registered user '{new_user.username}' with role '{new_user.role}'")
        
        # Log audit trail
        audit = AuditLog(
            user_id=new_user.id,
            action="user_register",
            entity_type="user",
            entity_id=new_user.id,
            description=f"User {new_user.username} registered with role {new_user.role}."
        )
        db.add(audit)
        db.commit()
        
    except Exception as exc:
        db.rollback()
        logger.error(f"Failed to register user: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to register user due to database error."
        )
        
    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Log in to receive JWT token credentials"
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    login_data: LoginRequest | None = None,
    form_data: Annotated[OAuth2PasswordRequestForm | None, Depends(OAuth2PasswordRequestForm)] = None,
    db: Session = Depends(get_db)
) -> dict:
    """Authenticate username/password and return access + refresh tokens.
    
    Supports standard JSON request payloads and URL form-encoded data.
    """
    username = None
    password = None

    # Handle standard OAuth2 password bearer form format
    if form_data:
        username = form_data.username
        password = form_data.password
    # Fallback to JSON payload
    elif login_data:
        username = login_data.username
        password = login_data.password

    if not username or not password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credentials not provided."
        )

    user = db.query(User).filter(
        User.username == username, 
        User.is_deleted == False
    ).first()
    
    if not user or not verify_password(password, user.password_hash):
        logger.warning(f"Failed login attempt for username: {username} from IP: {request.client.host if request.client else 'unknown'}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Generate tokens
    access_token = create_access_token(user.username, user.role)
    refresh_token = create_refresh_token(user.username, user.role)

    logger.info(f"Successful login for user '{user.username}'")

    # Record login audit log
    try:
        audit = AuditLog(
            user_id=user.id,
            action="user_login",
            entity_type="user",
            entity_id=user.id,
            description="User logged in successfully.",
            ip_address=request.client.host if request.client else None
        )
        db.add(audit)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(f"Audit log insertion failed on login: {exc}")

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": user
    }


@router.post(
    "/refresh",
    response_model=dict,
    summary="Obtain a new access token using a refresh token"
)
async def refresh(
    refresh_in: RefreshRequest,
    db: Session = Depends(get_db)
) -> dict:
    """Decodes a valid, unexpired refresh token to issue a new access token."""
    try:
        payload = jwt.decode(
            refresh_in.refresh_token, 
            settings.secret_key, 
            algorithms=[settings.algorithm]
        )
        
        # Verify type is "refresh"
        if payload.get("type") != "refresh":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Expected refresh token."
            )
            
        username: str | None = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token payload."
            )
            
    except jwt.exceptions.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token expired. Please re-authenticate."
        )
    except jwt.exceptions.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token signature."
        )

    user = db.query(User).filter(
        User.username == username, 
        User.is_deleted == False
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with this token not found."
        )

    # Issue new tokens
    new_access_token = create_access_token(user.username, user.role)
    new_refresh_token = create_refresh_token(user.username, user.role)

    return {
        "access_token": new_access_token,
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": user.role
        }
    }


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Retrieve current user details"
)
@router.get(
    "/profile",
    response_model=UserResponse,
    summary="Retrieve current user details (alias)"
)
async def get_me(
    current_user: User = Depends(get_current_user)
) -> User:
    """Return the profile of the currently logged-in user."""
    return current_user


@router.post(
    "/logout",
    summary="Invalidate active user session"
)
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    token: str | None = Depends(oauth2_scheme)
) -> dict:
    """Log out of the current user session and add audit entry."""
    logger.info(f"User '{current_user.username}' logged out.")
    
    # Blacklist the access token
    if token:
        from app.core.redis import blacklist_token
        from app.core.config import settings
        # Blacklist it for the duration of its expiry (15m default)
        blacklist_token(token, expires_in_seconds=settings.access_token_expire_minutes * 60)

    try:
        audit = AuditLog(
            user_id=current_user.id,
            action="user_logout",
            entity_type="user",
            entity_id=current_user.id,
            description="User logged out successfully."
        )
        db.add(audit)
        db.commit()
    except Exception as exc:
        db.rollback()
        logger.error(f"Audit log insertion failed on logout: {exc}")
        
    return {"success": True, "detail": "User session logged out."}
