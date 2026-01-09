from abc import ABC, abstractmethod
from typing import Dict, List

from .factory import get_embedding_model


class BaseVectorStore(ABC):
    """
    Abstract base class for Vector Stores.
    Handles common initialization logic like embedding model loading.
    """

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        provider: str = "local",
    ):
        """
        初始化向量存储基类。

        Args:
            model_name: 使用的 embedding 模型名称
            provider: 模型提供商 ("local" 或 "openai")
        """
        self.model_name = model_name
        self.provider = provider
        self.embedding_model = None

        # 如果使用的是 OpenAI 且模型名仍为默认的本地模型名，则自动调整为 OpenAI 的默认模型
        # Adjust default model name for OpenAI if it looks like the local default
        if self.provider == "openai" and self.model_name == "all-MiniLM-L6-v2":
            self.model_name = "text-embedding-3-small"

    def _init_model(self):
        """
        延迟初始化 Embedding 模型，避免在不需要时加载模型。
        子类在需要使用 self.embedding_model 前应调用此方法 (或 super()._init_resources())。
        """
        if self.embedding_model is None:
            self.embedding_model = get_embedding_model(self.provider, self.model_name)

    @abstractmethod
    def build_index(self, item_data_dir: str = "./data/item"):
        """从目录构建索引。"""
        pass

    @abstractmethod
    def search(self, query: str, k: int = 3) -> List[Dict]:
        """搜索最相似的 K 个物品。"""
        pass

    @abstractmethod
    def update_index(self, file_paths: List[str]):
        """增量更新索引。"""
        pass
