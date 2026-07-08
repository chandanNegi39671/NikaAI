import sys
from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings

# Initialize the global rate limiter using the client's IP address
# Fallback to in-memory storage during tests to avoid Redis connection errors
is_testing = "pytest" in sys.modules
storage_uri = "memory://" if is_testing else settings.redis_url

limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=storage_uri
)

