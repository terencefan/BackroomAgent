import logging
import time
import uuid
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

class MemoryItem:
    """
    Represents a single unit of memory with metadata.
    """
    def __init__(self, content: Dict[str, Any]):
        self.id: str = str(uuid.uuid4())
        self.content: Dict[str, Any] = content
        self.usage_count: int = 0
        self.created_at: float = time.time()
        self.last_used_at: float = self.created_at

    def touch(self):
        """Updates last used time and increments usage count."""
        self.usage_count += 1
        self.last_used_at = time.time()

class MemoryManager:
    """
    Manages memories for the agent.
    """
    _instances: Dict[str, "MemoryManager"] = {}

    @classmethod
    def get_instance(cls, session_id: str) -> "MemoryManager":
        """Returns the singleton instance for the given session_id."""
        if session_id not in cls._instances:
            cls._instances[session_id] = cls(session_id)
        return cls._instances[session_id]

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.memories: List[MemoryItem] = []

    def add_memory(self, content: Dict[str, Any]):
        """Adds a memory item with metadata."""
        item = MemoryItem(content)
        self.memories.append(item)
    
    def get_recent_memories(self, k: int = 5) -> List[MemoryItem]:
        """Retrieves the last k memories and updates their usage stats."""
        # Retrieve the relevant memories
        recent = self.memories[-k:]
        
        # Update usage stats
        for item in recent:
            item.touch()
            
        return recent

    def clear(self):
        """Clears all memories."""
        self.memories = []
