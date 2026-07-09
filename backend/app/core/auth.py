"""
backend/app/core/auth.py
────────────────────────
JWT Authentication & Role-Based Access Control logic.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import ExpiredSignatureError, PyJWTError
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.logging import get_logger
from app.models.db_models import User

logger = get_logger(__name__)

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme definition
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/login",
    auto_error=False,  # Allow custom verification and guest paths
)


# Defined Roles
class UserRole:
    ADMIN = "admin"
    SUPERVISOR = "supervisor"
    OPERATOR = "operator"
    VIEWER = "viewer"


# Role Hierarchy / Permissions mapping
# Admin can access everything
# Supervisor can access inspections, reports, analytics
# Operator can only inspect
# Viewer can only see the dashboard
ROLE_PERMISSIONS: Dict[str, List[str]] = {
    UserRole.ADMIN: ["*"],
    UserRole.SUPERVISOR: [
        "inspection:read",
        "inspection:write",
        "reports:read",
        "reports:write",
        "analytics:read",
    ],
    UserRole.OPERATOR: ["inspection:read", "inspection:write"],
    UserRole.VIEWER: ["analytics:read"],
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain text password matches its stored hash."""
    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception as exc:
        logger.error(f"Error verifying password: {exc}")
        return False


def get_password_hash(password: str) -> str:
    """Generate a secure bcrypt hash of a plain text password."""
    return pwd_context.hash(password)


def create_token(
    subject: str, role: str, token_type: str, expires_delta: timedelta | None = None
) -> str:
    """Generic JWT token creator."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        # Default access vs refresh tokens
        if token_type == "access":
            expire = now + timedelta(minutes=settings.access_token_expire_minutes)
        else:
            expire = now + timedelta(days=settings.refresh_token_expire_days)

    payload = {
        "sub": subject,
        "role": role,
        "type": token_type,
        "exp": expire,
        "iat": now,
    }
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_access_token(subject: str, role: str) -> str:
    """Create a short-lived access token."""
    return create_token(subject, role, "access")


def create_refresh_token(subject: str, role: str) -> str:
    """Create a long-lived refresh token."""
    return create_token(
        subject, role, "refresh", timedelta(days=settings.refresh_token_expire_days)
    )


async def get_current_user(
    token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)
) -> User:
    """Validate access token and return the authenticated User database object."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Access token missing.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    from app.core.redis import is_token_blacklisted

    if is_token_blacklisted(token):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been blacklisted (logged out).",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = jwt.decode(
            token, settings.secret_key, algorithms=[settings.algorithm]
        )

        # Verify token type is "access"
        if payload.get("type") != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token type. Expected access token.",
                headers={"WWW-Authenticate": "Bearer"},
            )

        username: str | None = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials. Subject missing.",
                headers={"WWW-Authenticate": "Bearer"},
            )

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired. Please log in again.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except PyJWTError as exc:
        logger.warning(f"JWT signature verification failed: {exc}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid signature or corrupted token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = (
        db.query(User)
        .filter(User.username == username, User.is_deleted == False)
        .first()
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account associated with this token not found.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


class PermissionChecker:
    """Dependency checker to enforce Role Based Access Control (RBAC)."""

    def __init__(self, required_permission: str) -> None:
        self.required_permission = required_permission

    def __call__(self, user: User = Depends(get_current_user)) -> User:
        user_role = user.role.lower()

        # Admin bypass
        if user_role == UserRole.ADMIN:
            return user

        allowed_perms = ROLE_PERMISSIONS.get(user_role, [])
        if "*" in allowed_perms or self.required_permission in allowed_perms:
            return user

        logger.warning(
            f"Access Denied: User '{user.username}' with role '{user.role}' "
            f"attempted to access permission '{self.required_permission}'"
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access Denied: Role '{user.role}' lacks permission '{self.required_permission}'",
        )


def verify_factory_scope(user: User, resource: Any) -> None:
    """Enforce multi-factory access limits: users can only access their assigned factory's resources."""
    user_role = user.role.lower()
    if user_role == UserRole.ADMIN:
        return  # Admin has global override access across all plants

    user_fid = getattr(user, "factory_id", None)
    res_fid = getattr(resource, "factory_id", None)

    if user_fid and res_fid and user_fid != res_fid:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: Resource belongs to another factory plant.",
        )
