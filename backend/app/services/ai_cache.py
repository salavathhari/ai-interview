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
        try:
            if redis is None:
                raise ImportError("redis not installed")
            host = os.getenv("REDIS_HOST", "localhost")
            password = os.getenv("REDIS_PASSWORD")
            self.redis = redis.Redis(host=host, port=6379, db=0, decode_responses=True, password=password)
            self.redis.ping()
            logger.info("✓ Connected to Redis for AI cache")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}. Redis is required for production.")
            raise

    def _get_key(self, prompt: str, model: str) -> str:
        # Create a unique hash for the prompt + model
        return hashlib.sha256(f"{model}:{prompt}".encode()).hexdigest()

    def get(self, prompt: str, model: str) -> Optional[dict]:
        key = self._get_key(prompt, model)
        data = self.redis.get(key)
        return json.loads(data) if data else None

    def set(self, prompt: str, model: str, response: dict, expire: int = 86400):
        key = self._get_key(prompt, model)
        self.redis.setex(key, expire, json.dumps(response))

ai_cache = AICache()
