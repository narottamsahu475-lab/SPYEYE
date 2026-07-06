import time
from typing import Dict, Any, Optional

class InMemoryCache:
    """Production fallback in-memory cache system with TTL expiration."""
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str) -> Optional[Any]:
        item = self._cache.get(key)
        if item and item["expires_at"] > time.time():
            return item["value"]
        if item:
            del self._cache[key]
        return None

    def set(self, key: str, value: Any, ttl: int = 900):
        self._cache[key] = {
            "value": value,
            "expires_at": time.time() + ttl
        }

cache_store = InMemoryCache()
