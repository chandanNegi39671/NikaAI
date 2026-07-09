"""
backend/app/core/database.py
──────────────────────────────
SQLAlchemy engine, session factory, and dependency injection.
"""

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker

from app.core.config import settings

# Database connection pool configurations based on dialect
connect_args = {}
pool_kwargs = {}

# Standardize postgresql vs postgres scheme for SQLAlchemy 1.4+
database_url = settings.database_url
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

if database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
else:
    # Production PostgreSQL connection pool tuning
    pool_kwargs = {
        "pool_size": 10,
        "max_overflow": 20,
        "pool_pre_ping": True,  # Pre-check database connections before checkout
        "pool_recycle": 1800,  # Recycle connections after 30 minutes to prevent stale links
    }

engine = create_engine(
    database_url, connect_args=connect_args, echo=settings.debug, **pool_kwargs
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """Dependency injection yield for SQLAlchemy sessions.

    Ensures session cleanup on request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
