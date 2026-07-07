# backend/app/api/__init__.py
# ─────────────────────────────────────────────────────────────────────────────
# Marks `api` as a Python package and re-exports the top-level versioned
# router so that main.py can do a single:
#
#     from app.api import router
#     app.include_router(router)
#
# All sub-routers (health, prediction, …) are assembled inside router.py.
# ─────────────────────────────────────────────────────────────────────────────

from app.api.router import router  # noqa: F401  (re-export)

__all__ = ["router"]
