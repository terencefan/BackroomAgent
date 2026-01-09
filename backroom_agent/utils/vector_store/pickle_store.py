import os
import pickle
from typing import Dict, List

import numpy as np

# 尝试导入 sklearn 依赖，如果没有安装则会在运行时报错提示
# Try to import sklearn dependency
try:
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    cosine_similarity = None

from .base import BaseVectorStore
from .loader import load_item_from_file, load_items_from_dir


class PickleVectorStore(BaseVectorStore):
    """
    一个简单的基于内存的向量存储实现。
    使用 numpy 存储向量矩阵，使用 pickle 序列化到磁盘。
    依赖 scikit-learn 计算余弦相似度。
    """

    def __init__(
        self,
        db_path: str = "./data/vector_store/item_vector_store.pkl",
        model_name: str = "all-MiniLM-L6-v2",
        provider: str = "local",
    ):
        """
        初始化向量存储。

        Args:
            db_path: 向量数据库文件保存路径 (.pkl)
            model_name: 使用的 embedding 模型名称
            provider: 模型提供商 ("local" 或 "openai")
        """
        super().__init__(model_name=model_name, provider=provider)
        self.db_path = db_path

    # _init_model is inherited, but we verify it works as intended.

    def build_index(self, item_data_dir: str = "./data/item"):
        """
        构建索引并保存。
        读取指定目录下的所有 JSON 文件，生成向量，并保存到磁盘。

        Args:
            item_data_dir: 包含 JSON 数据的目录路径
        """
        self._init_model()

        # 加载所有数据
        items = load_items_from_dir(item_data_dir)
        if not items:
            print("No items to index.")
            return

        print(f"Generating embeddings for {len(items)} items...")

        # 提取文本并生成向量
        texts = [item["text"] for item in items]
        embeddings = self.embedding_model.embed_documents(texts)
        embedding_matrix = np.array(embeddings)

        # 准备保存的数据结构
        data = {"items": items, "embedding_matrix": embedding_matrix}

        # 确保存储目录存在
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        # 序列化保存到文件
        with open(self.db_path, "wb") as f:
            pickle.dump(data, f)

        print(f"Save        to {self.db_path}")

    def search(self, query: str, k: int = 3) -> List[Dict]:
        """
        搜索物品。
        计算查询文本与库中所有物品的余弦相似度，返回前 k 个最相似的物品。

        Args:
            query: 查询文本
            k: 返回结果的数量

        Returns:
            包含物品信息和相似度分数的列表
        """
        if not os.path.exists(self.db_path):
            print(f"Index not found at {self.db_path}. Please build it first.")
            return []

        if cosine_similarity is None:
            raise ImportError(
                "Missing dependency 'scikit-learn'. Please install it via pip."
            )

        self._init_model()

        # 加载索引
        with open(self.db_path, "rb") as f:
            data = pickle.load(f)

        items = data["items"]
        matrix = data["embedding_matrix"]

        # 生成查询向量
        query_vec = self.embedding_model.embed_query(query)
        # 转换为 numpy 数组并调整形状 (1, dimension)
        query_vec = np.array(query_vec).reshape(1, -1)

        # 计算相似度
        scores = cosine_similarity(query_vec, matrix)[0]
        # 获取前 k 个最高分的索引 (::-1 用于逆序，从高到低)
        top_indices = scores.argsort()[-k:][::-1]

        results = []
        for idx in top_indices:
            score = scores[idx]
            item = items[idx]
            results.append(
                {"score": float(score), **item}  # 展开 item，包含 id, text, metadata
            )

        return results

    def update_index(self, file_paths: List[str]):
        """
        增量更新索引。
        仅重新计算新文件或修改文件的 embedding，避免全量重建。

        Args:
            file_paths: 需要更新的文件路径列表
        """
        if not file_paths:
            return

        self._init_model()

        # 1. 加载现有索引 Load existing index
        if os.path.exists(self.db_path):
            with open(self.db_path, "rb") as f:
                data = pickle.load(f)
            items = data["items"]  # List[Dict]
            embedding_matrix = data["embedding_matrix"]  # np.array
        else:
            items = []
            embedding_matrix = None

        # 建立 ID 到索引的映射，方便快速查找
        # Helper to find index by item id
        id_to_index = {item["id"]: i for i, item in enumerate(items)}

        new_items_data = []  # List of tuples (target_index, item_data)

        # 2. 处理输入文件 Process input files
        processed_count = 0
        for file_path in file_paths:
            item_dict = load_item_from_file(file_path)
            if not item_dict:
                continue

            item_id = item_dict["id"]
            target_idx = id_to_index.get(item_id, -1)
            # 记录是否已存在及其位置，如果不存在 target_idx 为 -1
            new_items_data.append({"target_index": target_idx, "item": item_dict})
            processed_count += 1

        if not new_items_data:
            print("No valid items found to update.")
            return

        # 3. 生成新数据的 Embeddings
        texts_to_embed = [x["item"]["text"] for x in new_items_data]

        print(
            f"Generating embeddings for {len(texts_to_embed)} items (Incremental update)..."
        )
        # 批量生成向量
        embeddings = self.embedding_model.embed_documents(texts_to_embed)
        new_embeddings_matrix = np.array(embeddings)

        # 4. 更新内部状态 Update internal state

        # 如果已有矩阵，则需要合并更新
        if embedding_matrix is not None:

            # 分离出“更新现有项”和“追加新项”
            updates = []
            appends = []

            for i, data in enumerate(new_items_data):
                target_idx = data["target_index"]
                vec = new_embeddings_matrix[i]
                item = data["item"]

                if target_idx >= 0:
                    updates.append((target_idx, item, vec))
                else:
                    appends.append((item, vec))

            # 应用更新 (替换旧值)
            for idx, item, vec in updates:
                items[idx] = item
                embedding_matrix[idx] = vec

            # 应用追加 (添加到末尾)
            if appends:
                new_items_list = [x[0] for x in appends]
                new_vecs_list = [x[1] for x in appends]
                items.extend(new_items_list)
                # 使用 vstack 堆叠矩阵
                embedding_matrix = np.vstack(
                    [embedding_matrix, np.array(new_vecs_list)]
                )

        else:
            # 如果是全新数据库
            items = [x["item"] for x in new_items_data]
            embedding_matrix = new_embeddings_matrix

        # 5. 保存 Save
        data = {"items": items, "embedding_matrix": embedding_matrix}

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, "wb") as f:
            pickle.dump(data, f)

        print(f"Updated index at {self.db_path}. Total items: {len(items)}")
