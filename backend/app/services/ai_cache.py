import hashlib
import json
import logging
try:
    import redis
except ImportError:
    redis = None
import os
from typing import Optional

logger = logging.getLogger(__name__)

# Redis-based cache for AI responses (required for multi-worker scalability)
class AICache:
    def __init__(self):
        self.redis = None
        try:
            if redis is None:
                logger.warning("redis package not installed — AI cache disabled")
                return
            host = os.getenv("REDIS_HOST", "localhost")
            password = os.getenv("REDIS_PASSWORD")
            self.redis = redis.Redis(host=host, port=6379, db=0, decode_responses=True, password=password)
            self.redis.ping()
            logger.info("✓ Connected to Redis for AI cache")
        except Exception as e:
            logger.warning(f"Redis unavailable — AI cache disabled: {e}")
            self.redis = None

    def _get_key(self, prompt: str, model: str) -> str:
        return hashlib.sha256(f"{model}:{prompt}".encode()).hexdigest()

    def get(self, prompt: str, model: str) -> Optional[dict]:
        if self.redis is None:
            return None
        key = self._get_key(prompt, model)
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def set(self, prompt: str, model: str, response: dict, expire: int = 86400):
        if self.redis is None:
            return
        key = self._get_key(prompt, model)
        self.redis.setex(key, expire, json.dumps(response))

ai_cache = AICache()
