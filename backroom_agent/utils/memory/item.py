import time
import uuid


class MemoryItem:
    """
    Represents a single unit of memory with metadata.
    """

    def __init__(self, content: str):
        self.id: str = str(uuid.uuid4())
        self.content: str = content
        self.usage_count: int = 0
        self.created_at: float = time.time()
        self.last_used_at: float = self.created_at

    def touch(self):
        """Updates last used time and increments usage count."""
        self.usage_count += 1
        self.last_used_at = time.time()
