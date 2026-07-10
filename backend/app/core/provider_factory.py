"""
backend/app/core/provider_factory.py
Runtime provider selection for LLM and knowledge adapters.
"""
from __future__ import annotations
import os
from app.core.llm_adapters import LLMAdapter, GoogleGemmaAdapter, RuleBasedAdapter
from app.core.logging import get_logger

logger = get_logger(__name__)

def get_llm_adapter() -> LLMAdapter:
    google_key = os.environ.get("GOOGLE_AI_KEY", "")
    if google_key:
        logger.info("LLM Provider: GoogleGemmaAdapter (Gemma 4)")
        return GoogleGemmaAdapter()
    logger.info("LLM Provider: RuleBasedAdapter (fallback)")
    return RuleBasedAdapter()

def get_knowledge_provider():
    """Returns keyword-based knowledge provider (default)."""
    try:
        from app.core.knowledge_providers import KeywordKnowledgeProvider
        return KeywordKnowledgeProvider()
    except ImportError:
        logger.warning("KeywordKnowledgeProvider not found, returning None")
        return None
