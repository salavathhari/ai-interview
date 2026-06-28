import hashlib
import json
import threading
try:
    import redis
except ImportError:
    redis = None
import os
from typing import Optional

# Simple Redis-based or In-Memory cache for AI responses
class AICache:
    def __init__(self):
        self._lock = threading.Lock()
        try:
            if redis is None:
                raise ImportError("redis not installed")
            # Attempt to connect to Redis, fallback to local dict if unavailable
            host = os.getenv("REDIS_HOST", "localhost")
            password = os.getenv("REDIS_PASSWORD")
            self.redis = redis.Redis(host=host, port=6379, db=0, decode_responses=True, password=password)
            self.redis.ping()
            self.use_redis = True
        except Exception:
            self.use_redis = False
            self.local_cache = {}

    def _get_key(self, prompt: str, model: str) -> str:
        # Create a unique hash for the prompt + model
        return hashlib.sha256(f"{model}:{prompt}".encode()).hexdigest()

    def get(self, prompt: str, model: str) -> Optional[dict]:
        key = self._get_key(prompt, model)
        if self.use_redis:
            data = self.redis.get(key)
            return json.loads(data) if data else None
        with self._lock:
            return self.local_cache.get(key)

    def set(self, prompt: str, model: str, response: dict, expire: int = 3600):
        key = self._get_key(prompt, model)
        if self.use_redis:
            self.redis.setex(key, expire, json.dumps(response))
        else:
            with self._lock:
                self.local_cache[key] = response

ai_cache = AICache()
