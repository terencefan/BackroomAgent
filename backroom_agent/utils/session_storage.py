"""Redis 会话存储抽象层"""

import json
from datetime import datetime
from typing import Any, Dict, Optional

import redis

from backroom_agent.constants import REDIS_HOST, REDIS_PASSWORD, REDIS_PORT
from backroom_agent.utils.logger import logger


class SessionStorage:
    """Redis 会话存储实现"""

    def __init__(self):
        self._client: Optional[redis.Redis] = None
        try:
            self._client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                password=REDIS_PASSWORD,
                decode_responses=True,
                socket_connect_timeout=1,
            )
            self._client.ping()
            logger.info(
                f"SessionStorage: Connected to Redis at {REDIS_HOST}:{REDIS_PORT}"
            )
        except redis.ConnectionError:
            logger.warning(
                f"SessionStorage: Could not connect to Redis at {REDIS_HOST}:{REDIS_PORT}. "
                "Sessions will only be stored in memory."
            )
            self._client = None

    def _get_key(self, session_id: str) -> str:
        """生成 Redis key"""
        return f"session:{session_id}"

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        """从 Redis 获取会话数据"""
        if not self._client:
            return None

        try:
            key = self._get_key(session_id)
            value = self._client.get(key)
            if value:
                # decode_responses=True ensures value is str
                return json.loads(str(value))
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.warning(f"SessionStorage: Error getting session {session_id}: {e}")

        return None

    def set(self, session_id: str, data: Dict[str, Any], ttl: int = 86400) -> bool:
        """保存会话数据到 Redis（TTL 默认 24 小时）"""
        if not self._client:
            return False

        try:
            key = self._get_key(session_id)
            value = json.dumps(data, ensure_ascii=False, default=str)
            self._client.setex(key, ttl, value)
            return True
        except (redis.RedisError, TypeError) as e:
            logger.warning(f"SessionStorage: Error setting session {session_id}: {e}")
            return False

    def delete(self, session_id: str) -> bool:
        """删除会话数据"""
        if not self._client:
            return False

        try:
            key = self._get_key(session_id)
            self._client.delete(key)
            return True
        except redis.RedisError as e:
            logger.warning(f"SessionStorage: Error deleting session {session_id}: {e}")
            return False

    def exists(self, session_id: str) -> bool:
        """检查会话是否存在"""
        if not self._client:
            return False

        try:
            key = self._get_key(session_id)
            return bool(self._client.exists(key))
        except redis.RedisError:
            return False
