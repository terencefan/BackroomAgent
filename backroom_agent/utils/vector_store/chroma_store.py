import os
import shutil
from typing import Any, Dict, List, Optional, cast

import chromadb
from chromadb.config import Settings

from .base import BaseVectorStore
from .loader import load_item_from_file, load_items_from_dir


class ChromaVectorStore(BaseVectorStore):
    """
    基于 ChromaDB 的向量存储实现。
    支持持久化存储、增量更新和高效检索。
    """

    def __init__(
        self,
        collection_name: str = "item_collection",
        persist_directory: str = "./data/vector_store/chroma_db",
        model_name: str = "all-MiniLM-L6-v2",
        provider: str = "local",
    ):
        """
        初始化 Chroma 向量存储。

        Args:
            collection_name: Chroma 集合名称
            persist_directory: 数据库持久化目录
            model_name: 使用的 embedding 模型名称
            provider: 模型提供商 ("local" 或 "openai")
        """
        super().__init__(model_name=model_name, provider=provider)
        self.collection_name = collection_name
        self.persist_directory = persist_directory
        self.client = None
        self.collection = None

    def _init_resources(self):
        """初始化 Embedding 模型和 Chroma 客户端。"""
        self._init_model()  # Inherited from BaseVectorStore

        if self.client is None:
            # 初始化持久化客户端
            os.makedirs(self.persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(path=self.persist_directory)

            # 获取或创建集合
            # We don't pass an embedding function here because we generate embeddings manually
            # using our own factory/model before passing to Chroma.
            # This allows us to keep the embedding logic consistent across stores.
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name
            )

    def build_index(self, item_data_dir: str = "./data/item"):
        """
        构建索引并保存。
        注意：这会重置当前的 Collection。
        """
        self._init_resources()
        assert self.client is not None
        assert self.collection is not None
        assert self.embedding_model is not None

        items = load_items_from_dir(item_data_dir)
        if not items:
            print("No items to index.")
            return

        print(f"Resetting collection '{self.collection_name}'...")
        self.client.delete_collection(self.collection_name)
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name
        )

        print(f"Generating embeddings for {len(items)} items...")

        # Batch processing to avoid memory issues with large datasets
        batch_size = 100
        for i in range(0, len(items), batch_size):
            batch_items = items[i : i + batch_size]
            batch_texts = [item["text"] for item in batch_items]
            batch_ids = [item["id"] for item in batch_items]
            # Convert metadata values to strings or basic types if needed,
            # but our items are usually simple dicts.
            # Chroma requires metadata values to be str, int, float, bool.
            # We filter metadata just in case.
            batch_metadatas = []
            for item in batch_items:
                meta = {}
                for k, v in item.items():
                    if k == "text":
                        continue  # text is separate
                    if isinstance(v, (str, int, float, bool)):
                        meta[k] = v
                    else:
                        meta[k] = str(v)
                batch_metadatas.append(meta)

            embeddings = self.embedding_model.embed_documents(batch_texts)

            self.collection.add(
                documents=batch_texts,
                embeddings=cast(Any, embeddings),
                metadatas=batch_metadatas,
                ids=batch_ids,
            )
            print(
                f"Indexed batch {i // batch_size + 1}/{(len(items) + batch_size - 1) // batch_size}"
            )

        print(f"Saved index to {self.persist_directory}")

    def search(self, query: str, k: int = 3) -> List[Dict]:
        """搜索物品。"""
        self._init_resources()
        assert self.collection is not None
        assert self.embedding_model is not None

        # Generate query embedding
        query_vec = self.embedding_model.embed_query(query)

        results = self.collection.query(
            query_embeddings=[query_vec],
            n_results=k,
            include=["documents", "metadatas", "distances"],
        )

        # Parse results
        # Chroma returns lists of lists (one for each query)
        parsed_results = []
        if (
            results["ids"]
            and len(results["ids"]) > 0
            and results["metadatas"]
            and results["documents"]
        ):
            ids = results["ids"][0]
            metadatas = results["metadatas"][0]
            documents = results["documents"][0]
            distances = (
                results["distances"][0] if results["distances"] else [0.0] * len(ids)
            )

            for i in range(len(ids)):
                # Convert distance to a similarity score (approximate)
                # L2 distance: lower is better. Cosine distance: lower is better.
                # Assuming simple cosine distance, similarity = 1 - distance.
                # PickleStore used cosine_similarity which is -1 to 1.
                # Here we just return the score/distance as is or invert it if needed.
                # Let's align with PickleStore: output "score".
                # Note: Chroma default is L2.
                # For consistency with PickleStore (cosine sim), we might want to check
                # if we can configure Chroma to use cosine.
                # But for now, we just pass what we get.

                item = cast(Dict[str, Any], metadatas[i]).copy()
                item["id"] = ids[i]
                item["text"] = documents[i]

                # If using cosine distance, similarity = 1 - distance
                # If using L2, it's not directly comparable.
                # But typically we just want to sort.
                parsed_results.append(
                    {
                        "score": float(
                            distances[i]
                        ),  # Note: This is usually distance, not similarity
                        **item,
                    }
                )

        return parsed_results

    def update_index(self, file_paths: List[str]):
        """
        增量更新索引。
        """
        if not file_paths:
            return

        self._init_resources()
        assert self.collection is not None
        assert self.embedding_model is not None

        new_items = []
        for file_path in file_paths:
            item = load_item_from_file(file_path)
            if item:
                new_items.append(item)

        if not new_items:
            return

        print(f"Updating {len(new_items)} items in ChromaDB...")

        texts = [item["text"] for item in new_items]
        ids = [item["id"] for item in new_items]
        metadatas = []
        for item in new_items:
            meta = {}
            for k, v in item.items():
                if k == "text":
                    continue
                if isinstance(v, (str, int, float, bool)):
                    meta[k] = v
                else:
                    meta[k] = str(v)
            metadatas.append(meta)

        embeddings = self.embedding_model.embed_documents(texts)

        # Upsert (insert or update)
        self.collection.upsert(
            ids=ids,
            embeddings=cast(Any, embeddings),
            metadatas=metadatas,
            documents=texts,
        )
        print(f"Updated {len(new_items)} items.")
