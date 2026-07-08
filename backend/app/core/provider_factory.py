"""
backend/app/core/provider_factory.py
────────────────────────────────────
Factory class to instantiate and cache LLM adapters and Knowledge providers based on configuration.
"""

from app.core.config import settings
from app.core.llm_adapters import (
    LLMAdapter,
    RuleBasedAdapter,
    OllamaAdapter,
    GemmaAdapter,
    OpenAIAdapter,
    HuggingFaceAdapter,
)
from app.core.knowledge_providers import (
    KnowledgeProvider,
    KeywordKnowledgeProvider,
    VectorKnowledgeProvider,
)
from app.core.logging import get_logger

logger = get_logger(__name__)

# Singletons for memory efficiency
_llm_cache: dict[str, LLMAdapter] = {}
_kp_cache: dict[str, KnowledgeProvider] = {}

def get_llm_adapter() -> LLMAdapter:
    """Instantiate and return the configured LLMAdapter."""
    provider_name = settings.llm_provider.lower().strip()
    
    if provider_name in _llm_cache:
        return _llm_cache[provider_name]
        
    logger.info(f"Initializing LLM adapter: '{provider_name}'")
    
    if provider_name == "rule_based":
        adapter = RuleBasedAdapter()
    elif provider_name == "ollama":
        adapter = OllamaAdapter()
    elif provider_name == "gemma":
        adapter = GemmaAdapter()
    elif provider_name == "openai":
        adapter = OpenAIAdapter()
    elif provider_name == "huggingface":
        adapter = HuggingFaceAdapter()
    else:
        logger.warning(f"Unknown LLM provider '{provider_name}'. Defaulting to 'rule_based'.")
        adapter = RuleBasedAdapter()
        
    _llm_cache[provider_name] = adapter
    return adapter

def get_knowledge_provider() -> KnowledgeProvider:
    """Instantiate and return the configured KnowledgeProvider."""
    provider_name = settings.knowledge_provider.lower().strip()
    
    if provider_name in _kp_cache:
        return _kp_cache[provider_name]
        
    logger.info(f"Initializing Knowledge provider: '{provider_name}'")
    
    if provider_name == "keyword":
        provider = KeywordKnowledgeProvider()
    elif provider_name == "vector":
        provider = VectorKnowledgeProvider()
    else:
        logger.warning(f"Unknown Knowledge provider '{provider_name}'. Defaulting to 'keyword'.")
        provider = KeywordKnowledgeProvider()
        
    _kp_cache[provider_name] = provider
    return provider
