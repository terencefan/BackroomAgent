import glob
import json
import os
import pickle
from typing import Dict, List, Optional

import numpy as np

# 尝试导入依赖
try:
    from langchain_huggingface import HuggingFaceEmbeddings
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    # 如果作为库被导入但依赖缺失，可能需要在运行时报错，或者在这里处理
    HuggingFaceEmbeddings = None
    cosine_similarity = None


class SimpleVectorStore:
    def __init__(
        self,
        db_path: str = "./data/vector_store/item_vector_store.pkl",
        model_name: str = "all-MiniLM-L6-v2",
    ):
        self.db_path = db_path
        self.model_name = model_name
        self.embedding_model = None

    def _init_model(self):
        if self.embedding_model is None:
            if HuggingFaceEmbeddings is None:
                raise ImportError(
                    "Missing dependencies: pip install langchain-huggingface sentence-transformers scikit-learn"
                )
            print(f"Initializing embedding model ({self.model_name})...")
            self.embedding_model = HuggingFaceEmbeddings(model_name=self.model_name)

    def load_items_from_dir(self, item_data_dir: str = "./data/item") -> List[Dict]:
        """遍历目录下的所有 JSON 文件，读取物品信息。"""
        items = []
        # 递归查找所有 .json 文件
        search_pattern = os.path.join(item_data_dir, "**", "*.json")
        files = glob.glob(search_pattern, recursive=True)

        print(f"Found {len(files)} item files in {item_data_dir}.")

        for file_path in files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # 提取关键字段
                name = data.get("name", "Unknown")
                description = data.get("description", "")
                category = data.get("category", None)
                behavior = data.get("behavior", None)  # For entities
                item_id = data.get(
                    "id", os.path.basename(file_path).replace(".json", "")
                )

                # 构造用于 Embedding 的文本内容
                if category:
                    text = f"Item: {name}\nCategory: {category}\nDescription: {description}"
                elif behavior:
                    text = f"Entity: {name}\nBehavior: {behavior}\nDescription: {description}"
                else:
                    text = f"Object: {name}\nDescription: {description}"

                items.append(
                    {
                        "id": item_id,
                        "text": text,
                        "metadata": {
                            "name": name,
                            "category": category,
                            "behavior": behavior,
                            "description": description,
                            "path": file_path,
                            "raw_data": data,  # 保存原始数据以便使用
                        },
                    }
                )
            except Exception as e:
                print(f"Warning loading {file_path}: {e}")

        return items

    def build_index(self, item_data_dir: str = "./data/item"):
        """构建索引并保存。"""
        self._init_model()

        items = self.load_items_from_dir(item_data_dir)
        if not items:
            print("No items to index.")
            return

        print(
            f"Generating embeddings for {len(items)} items... (This happens locally on CPU)"
        )

        texts = [item["text"] for item in items]
        embeddings = self.embedding_model.embed_documents(texts)
        embedding_matrix = np.array(embeddings)

        data = {"items": items, "embedding_matrix": embedding_matrix}

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)

        with open(self.db_path, "wb") as f:
            pickle.dump(data, f)

        print(f"Saved index to {self.db_path}")

    def search(self, query: str, k: int = 3) -> List[Dict]:
        """搜索物品。"""
        if not os.path.exists(self.db_path):
            print(f"Index not found at {self.db_path}. Please build it first.")
            return []

        self._init_model()

        with open(self.db_path, "rb") as f:
            data = pickle.load(f)

        items = data["items"]
        matrix = data["embedding_matrix"]

        query_vec = self.embedding_model.embed_query(query)
        query_vec = np.array(query_vec).reshape(1, -1)

        scores = cosine_similarity(query_vec, matrix)[0]
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
        Incrementally update the index with new or modified files.
        Only re-calculates embeddings for the provided files.
        """
        if not file_paths:
            return

        self._init_model()

        # 1. Load existing index
        if os.path.exists(self.db_path):
            with open(self.db_path, "rb") as f:
                data = pickle.load(f)
            items = data["items"]  # List[Dict]
            embedding_matrix = data["embedding_matrix"]  # np.array
        else:
            items = []
            embedding_matrix = None

        # Helper to find index by item id
        id_to_index = {item["id"]: i for i, item in enumerate(items)}

        new_items_data = []  # List of tuples (target_index, item_data)

        # 2. Process input files
        processed_count = 0
        for file_path in file_paths:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)

                # Extract fields (Same logic as load_items_from_dir)
                name = data.get("name", "Unknown")
                description = data.get("description", "")
                category = data.get("category", None)
                behavior = data.get("behavior", None)
                item_id = data.get(
                    "id", os.path.basename(file_path).replace(".json", "")
                )

                if category:
                    text = f"Item: {name}\nCategory: {category}\nDescription: {description}"
                elif behavior:
                    text = f"Entity: {name}\nBehavior: {behavior}\nDescription: {description}"
                else:
                    text = f"Object: {name}\nDescription: {description}"

                item_dict = {
                    "id": item_id,
                    "text": text,
                    "metadata": {
                        "name": name,
                        "category": category,
                        "behavior": behavior,
                        "description": description,
                        "path": file_path,
                        "raw_data": data,
                    },
                }

                target_idx = id_to_index.get(item_id, -1)
                new_items_data.append({"target_index": target_idx, "item": item_dict})
                processed_count += 1
            except Exception as e:
                print(f"Warning processing {file_path}: {e}")

        if not new_items_data:
            print("No valid items found to update.")
            return

        # 3. Generate embeddings for updates
        texts_to_embed = [x["item"]["text"] for x in new_items_data]

        print(
            f"Generating embeddings for {len(texts_to_embed)} items (Incremental update)..."
        )
        # In case the list is large, we could batch it, but usually incremental is small
        embeddings = self.embedding_model.embed_documents(texts_to_embed)
        new_embeddings_matrix = np.array(embeddings)

        # 4. Update internal state
        # We need to handle appends and updates carefully.
        # It's easier to reconstruct the lists.

        # If we have existing matrix
        if embedding_matrix is not None:
            # Convert to list for easier manipulation might be slow for huge DB, but fine here
            # Actually, let's keep it numpy.

            # Separate updates and appends
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

            # Apply updates
            for idx, item, vec in updates:
                items[idx] = item
                embedding_matrix[idx] = vec

            # Apply appends
            if appends:
                new_items_list = [x[0] for x in appends]
                new_vecs_list = [x[1] for x in appends]
                items.extend(new_items_list)
                embedding_matrix = np.vstack(
                    [embedding_matrix, np.array(new_vecs_list)]
                )

        else:
            # New DB
            items = [x["item"] for x in new_items_data]
            embedding_matrix = new_embeddings_matrix

        # 5. Save
        data = {"items": items, "embedding_matrix": embedding_matrix}

        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        with open(self.db_path, "wb") as f:
            pickle.dump(data, f)

        print(f"Updated index at {self.db_path}. Total items: {len(items)}")


# 为了方便直接调用，提供一个单例或辅助函数
def rebuild_vector_db(
    item_dir: str = "./data/item",
    db_path: str = "./data/vector_store/item_vector_store.pkl",
):
    store = SimpleVectorStore(db_path=db_path)
    store.build_index(item_data_dir=item_dir)


def update_vector_db(
    file_paths: List[str], db_path: str = "./data/vector_store/item_vector_store.pkl"
):
    """增量更新向量数据库"""
    store = SimpleVectorStore(db_path=db_path)
    store.update_index(file_paths)


def search_similar_items(
    query: str, k: int = 3, db_path: str = "./data/vector_store/item_vector_store.pkl"
) -> List[Dict]:
    store = SimpleVectorStore(db_path=db_path)
    return store.search(query, k=k)


if __name__ == "__main__":
    # 测试代码
    rebuild_vector_db()
    results = search_similar_items("something weapon")
    for res in results:
        print(f"[{res['score']:.4f}] {res['metadata']['name']}")
