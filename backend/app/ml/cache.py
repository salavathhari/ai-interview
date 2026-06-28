"""Simple in-memory LRU cache for ML prediction results."""

import hashlib
import time
from typing import Optional, Any


class MLCache:
    """LRU cache for ML results with TTL expiration."""

    def __init__(self, max_size: int = 512, ttl_seconds: int = 3600):
        self._cache: dict[str, tuple[float, Any]] = {}
        self._max_size = max_size
        self._ttl = ttl_seconds

    def make_key(self, prefix: str, text: str, **kwargs) -> str:
        raw = f"{prefix}:{text}:{sorted(kwargs.items())}"
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, key: str) -> Optional[Any]:
        if key in self._cache:
            timestamp, value = self._cache[key]
            if time.time() - timestamp < self._ttl:
                return value
            else:
                del self._cache[key]
        return None

    def set(self, key: str, value: Any):
        if len(self._cache) >= self._max_size:
            oldest_key = min(self._cache, key=lambda k: self._cache[k][0])
            del self._cache[oldest_key]
        self._cache[key] = (time.time(), value)

    def cached(self, prefix: str, text: str, fn, **kwargs):
        """Get from cache or compute and store."""
        key = self.make_key(prefix, text, **kwargs)
        result = self.get(key)
        if result is not None:
            return result, True
        result = fn(text, **kwargs)
        self.set(key, result)
        return result, False

    def clear(self):
        self._cache.clear()


ml_cache = MLCache(max_size=512, ttl_seconds=3600)
