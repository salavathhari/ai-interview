import hashlib
import logging
try:
    import redis
except ImportError:
    redis = None
import os
from typing import Optional

logger = logging.getLogger(__name__)


class TTSCache:
    """Redis-based cache for OpenAI TTS (text-to-speech) audio responses."""

    def __init__(self):
        try:
            if redis is None:
                raise ImportError("redis not installed")
            host = os.getenv("REDIS_HOST", "localhost")
            password = os.getenv("REDIS_PASSWORD")
            self.redis = redis.Redis(host=host, port=6379, db=1, decode_responses=False, password=password)
            self.redis.ping()
            logger.info("✓ Connected to Redis for TTS cache (db=1)")
        except Exception as e:
            logger.error(f"Failed to connect to Redis for TTS cache: {e}")
            raise

    def _get_key(self, text: str) -> str:
        """Create cache key from question text hash."""
        return f"tts:{hashlib.sha256(text.encode()).hexdigest()}"

    def get(self, text: str) -> Optional[bytes]:
        """Retrieve cached audio bytes for question text."""
        key = self._get_key(text)
        try:
            audio_bytes = self.redis.get(key)
            if audio_bytes:
                logger.debug(f"TTS cache hit for key {key[:20]}...")
            return audio_bytes
        except Exception as e:
            logger.error(f"Redis get failed: {e}")
            return None

    def set(self, text: str, audio_bytes: bytes, expire: int = 604800):
        """Cache audio bytes for question text. TTL: 7 days by default."""
        key = self._get_key(text)
        try:
            self.redis.setex(key, expire, audio_bytes)
            logger.debug(f"TTS cached for key {key[:20]}... (size: {len(audio_bytes)} bytes)")
        except Exception as e:
            logger.error(f"Redis set failed: {e}")

    def clear_pattern(self, pattern: str = "tts:*"):
        """Clear all TTS cache entries (use cautiously)."""
        try:
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
                logger.info(f"Cleared {len(keys)} TTS cache entries")
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")


# Singleton instance
tts_cache = TTSCache()
