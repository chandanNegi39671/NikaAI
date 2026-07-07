"""
backend/app/core/database.py
──────────────────────────────
SQLAlchemy engine, session factory, and dependency injection.
"""

from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

from app.core.config import settings

# For SQLite, allow multiple threads to access the connection
connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args,
    echo=False,  # Set to True in debug if needed
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
