import hashlib
import logging
from typing import Any, Callable, Optional

import redis

from backroom_agent.constants import REDIS_HOST, REDIS_PASSWORD, REDIS_PORT

logger = logging.getLogger(__name__)


class RedisCache:
    _instance = None
    _client: Optional[redis.Redis] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(RedisCache, cls).__new__(cls)
            try:
                cls._instance._client = redis.Redis(
                    host=REDIS_HOST,
                    port=REDIS_PORT,
                    password=REDIS_PASSWORD,
                    decode_responses=True,  # Return strings instead of bytes
                    socket_connect_timeout=1,  # Fast fail if redis is down
                )
                # Test connection
                cls._instance._client.ping()
                logger.info(f"Connected to Redis at {REDIS_HOST}:{REDIS_PORT}")
            except redis.ConnectionError:
                logger.warning(
                    f"Could not connect to Redis at {REDIS_HOST}:{REDIS_PORT}. Cache will be disabled/fallback."
                )
                cls._instance._client = None

        return cls._instance

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _generate_key(self, prefix: str, content: str) -> str:
        """Generates a cache key based on a prefix and the hash of the content."""
        content_hash = hashlib.md5(content.encode("utf-8")).hexdigest()
        return f"backroom:{prefix}:{content_hash}"

    def get(
        self, prefix: str, content: str, on_miss: Optional[Callable[[], Any]] = None
    ) -> Optional[Any]:
        """
        Retrieves a value from the cache.
        If on_miss is provided and cache is missing, executes on_miss(), caches result, and returns it.
        """
        key = self._generate_key(prefix, content)

        # Try read from Redis
        if self._client:
            try:
                value = self._client.get(key)
                if value is not None:
                    return value
            except redis.RedisError as e:
                logger.warning(f"Redis get error: {e}")

        # Cache Miss
        if on_miss:
            result = on_miss()
            if self._client and result:
                try:
                    # Default TTL 24 hours
                    self._client.setex(key, 86400, str(result))
                except redis.RedisError as e:
                    logger.warning(f"Redis set error: {e}")
            return result

        return None

    def set(self, prefix: str, content: str, value: Any) -> None:
        """Sets a value in the cache."""
        key = self._generate_key(prefix, content)
        if self._client:
            try:
                self._client.setex(key, 86400, str(value))
            except redis.RedisError as e:
                logger.warning(f"Redis set error: {e}")


# Global instance
memory_cache = RedisCache()
