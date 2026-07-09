"""
backend/run.py
──────────────
Development server runner for Nika AI backend.

Run from the `backend/` directory:
    python run.py

This is a convenience wrapper around uvicorn. In production, use:
    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
"""

import uvicorn

from app.core.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.reload,
        log_level=settings.log_level.lower(),
    )
