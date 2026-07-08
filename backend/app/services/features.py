"""
backend/app/services/features.py
────────────────────────────────
Feature flag manager with runtime Redis overrides and local fallbacks.
"""

from app.core.redis import cache_get, cache_set
from app.core.logging import get_logger

logger = get_logger(__name__)

# Default hardcoded feature statuses
DEFAULT_FEATURES = {
    "gemma_explanations": True,
    "analytics_dashboard": True,
    "notifications_slack": True,
    "notifications_email": True,
    "websocket_live": True,
    "predictive_maintenance": True,
}

def is_feature_enabled(feature_name: str) -> bool:
    """Return True if the specified feature flag is active."""
    # Check Redis override first
    cache_key = f"feature_flag:{feature_name}"
    override = cache_get(cache_key)
    if override is not None:
        return override.lower() == "true"
        
    # Return default status
    return DEFAULT_FEATURES.get(feature_name, False)

def set_feature_override(feature_name: str, enabled: bool) -> None:
    """Dynamically switch feature flag status without deploying/rebooting."""
    cache_key = f"feature_flag:{feature_name}"
    cache_set(cache_key, "true" if enabled else "false")
    logger.info(f"Feature override set: '{feature_name}' = {enabled}")
