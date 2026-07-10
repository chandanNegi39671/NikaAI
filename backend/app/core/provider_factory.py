"""
backend/app/core/provider_factory.py
──────────────────────────────────────
Runtime provider selection for LLM and knowledge adapters.

Selection logic:
  1. If settings.google_ai_key is set  → GoogleGeminiAdapter (Gemini / Gemma via Google AI Studio)
  2. Otherwise                          → RuleBasedAdapter (zero external deps, always works)

The knowledge provider defaults to KeywordKnowledgeProvider (SQL LIKE search).
A VectorKnowledgeProvider extension point is reserved for Sprint 9+.
"""

from __future__ import annotations

from app.core.config import settings
from app.core.llm_adapters import GoogleGeminiAdapter, LLMAdapter, RuleBasedAdapter
from app.core.logging import get_logger

logger = get_logger(__name__)


def get_llm_adapter() -> LLMAdapter:
    """Return the configured LLM adapter.

    Automatically promotes to GoogleGeminiAdapter when GOOGLE_AI_KEY is present
    in settings (loaded from environment or .env file).  Falls back gracefully
    to RuleBasedAdapter when no API key is configured so the service is always
    available without external dependencies.
    """
    if settings.google_ai_key:
        logger.info(
            "LLM Provider: GoogleGeminiAdapter",
            extra={"model": settings.google_ai_model},
        )
        return GoogleGeminiAdapter()

    logger.info("LLM Provider: RuleBasedAdapter (no GOOGLE_AI_KEY configured)")
    return RuleBasedAdapter()


def get_knowledge_provider():
    """Return the configured knowledge retrieval provider.

    Defaults to KeywordKnowledgeProvider (SQL LIKE search, zero external deps).
    Switch to VectorKnowledgeProvider in Sprint 9 by setting
    KNOWLEDGE_PROVIDER=vector and implementing VectorKnowledgeProvider.
    """
    try:
        from app.core.knowledge_providers import KeywordKnowledgeProvider

        return KeywordKnowledgeProvider()
    except ImportError:
        logger.warning(
            "KeywordKnowledgeProvider import failed — knowledge context unavailable"
        )
        return None
