"""会话管理器：管理游戏会话的状态和消息历史"""

import json
from datetime import datetime
from typing import Any, Dict, List, Optional

from langchain_core.messages import BaseMessage

from backroom_agent.protocol import GameState
from backroom_agent.utils.logger import logger
from backroom_agent.utils.session_storage import SessionStorage


class SessionData:
    """会话数据模型"""

    def __init__(
        self,
        session_id: str,
        messages: Optional[List[BaseMessage]] = None,
        game_state: Optional[GameState] = None,
    ):
        self.session_id = session_id
        self.messages: List[BaseMessage] = messages or []
        self.game_state: Optional[GameState] = game_state
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典（用于序列化）"""
        # 将 BaseMessage 转换为字典
        messages_dict = []
        for msg in self.messages:
            if hasattr(msg, "content") and hasattr(msg, "type"):
                messages_dict.append(
                    {
                        "type": msg.type,
                        "content": msg.content,
                    }
                )

        return {
            "session_id": self.session_id,
            "messages": messages_dict,
            "game_state": self.game_state.model_dump() if self.game_state else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionData":
        """从字典创建（用于反序列化）"""
        from langchain_core.messages import (AIMessage, HumanMessage,
                                             SystemMessage)

        # 恢复消息
        messages = []
        for msg_dict in data.get("messages", []):
            msg_type = msg_dict.get("type")
            content = msg_dict.get("content", "")
            if msg_type == "human":
                messages.append(HumanMessage(content=content))
            elif msg_type == "ai":
                messages.append(AIMessage(content=content))
            elif msg_type == "system":
                messages.append(SystemMessage(content=content))

        # 恢复游戏状态
        game_state = None
        if data.get("game_state"):
            game_state = GameState(**data["game_state"])

        session = cls(
            session_id=data["session_id"],
            messages=messages,
            game_state=game_state,
        )
        session.created_at = datetime.fromisoformat(
            data.get("created_at", datetime.now().isoformat())
        )
        session.updated_at = datetime.fromisoformat(
            data.get("updated_at", datetime.now().isoformat())
        )
        return session


class SessionManager:
    """会话管理器：管理内存和 Redis 中的会话数据"""

    def __init__(self):
        self._memory_cache: Dict[str, SessionData] = {}
        self._storage = SessionStorage()

    def create_or_reset_session(
        self, session_id: str, initial_state: Optional[GameState] = None
    ) -> SessionData:
        """
        创建新会话或重置已有会话（init 事件使用）
        清空消息历史，重新开始
        """
        session = SessionData(
            session_id=session_id,
            messages=[],
            game_state=initial_state,
        )
        self._memory_cache[session_id] = session
        self._save_to_storage(session)
        logger.info(f"SessionManager: Created/reset session {session_id}")
        return session

    def get_or_create_session(
        self, session_id: str, initial_state: Optional[GameState] = None
    ) -> SessionData:
        """
        获取会话，不存在则创建（message 事件使用）
        通常应该先有 init 事件，但如果没有则创建空会话
        """
        session = self.get_session(session_id)
        if session is None:
            session = SessionData(
                session_id=session_id,
                messages=[],
                game_state=initial_state,
            )
            self._memory_cache[session_id] = session
            self._save_to_storage(session)
            logger.info(
                f"SessionManager: Created new session {session_id} (no init found)"
            )
        return session

    def get_session(self, session_id: str) -> Optional[SessionData]:
        """获取会话（优先内存，fallback Redis）"""
        # 先查内存
        if session_id in self._memory_cache:
            return self._memory_cache[session_id]

        # 再查 Redis
        data = self._storage.get(session_id)
        if data:
            try:
                session = SessionData.from_dict(data)
                self._memory_cache[session_id] = session  # 缓存到内存
                return session
            except Exception as e:
                logger.error(
                    f"SessionManager: Error deserializing session {session_id}: {e}"
                )

        return None

    def update_session(
        self,
        session_id: str,
        messages: Optional[List[BaseMessage]] = None,
        game_state: Optional[GameState] = None,
    ) -> bool:
        """更新会话"""
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"SessionManager: Session {session_id} not found for update")
            return False

        if messages is not None:
            session.messages = messages
        if game_state is not None:
            session.game_state = game_state

        session.updated_at = datetime.now()
        self._memory_cache[session_id] = session
        self._save_to_storage(session)
        return True

    def add_message(self, session_id: str, message: BaseMessage) -> bool:
        """添加消息到会话"""
        session = self.get_session(session_id)
        if not session:
            logger.warning(
                f"SessionManager: Session {session_id} not found for add_message"
            )
            return False

        session.messages.append(message)
        session.updated_at = datetime.now()
        self._memory_cache[session_id] = session
        self._save_to_storage(session)
        return True

    def get_messages(self, session_id: str) -> List[BaseMessage]:
        """获取会话的消息历史"""
        session = self.get_session(session_id)
        if session:
            return session.messages
        return []

    def clear_session(self, session_id: str) -> bool:
        """清空会话（用于重建）"""
        if session_id in self._memory_cache:
            del self._memory_cache[session_id]
        self._storage.delete(session_id)
        logger.info(f"SessionManager: Cleared session {session_id}")
        return True

    def _save_to_storage(self, session: SessionData) -> None:
        """保存会话到 Redis"""
        try:
            data = session.to_dict()
            self._storage.set(session.session_id, data, ttl=86400)  # 24 小时
        except Exception as e:
            logger.warning(
                f"SessionManager: Error saving session {session.session_id} to storage: {e}"
            )


# 全局单例
_session_manager: Optional[SessionManager] = None


def get_session_manager() -> SessionManager:
    """获取全局会话管理器实例"""
    global _session_manager
    if _session_manager is None:
        _session_manager = SessionManager()
    return _session_manager
