import os
import glob
import json
import pickle
import numpy as np
from typing import List, Dict, Optional

# 尝试导入依赖
try:
    from langchain_huggingface import HuggingFaceEmbeddings
    from sklearn.metrics.pairwise import cosine_similarity
except ImportError:
    # 如果作为库被导入但依赖缺失，可能需要在运行时报错，或者在这里处理
    HuggingFaceEmbeddings = None
    cosine_similarity = None

class SimpleVectorStore:
    def __init__(self, db_path: str = "./data/simple_vector_store.pkl", model_name: str = "all-MiniLM-L6-v2"):
        self.db_path = db_path
        self.model_name = model_name
        self.embedding_model = None
        
    def _init_model(self):
        if self.embedding_model is None:
            if HuggingFaceEmbeddings is None:
                raise ImportError("Missing dependencies: pip install langchain-huggingface sentence-transformers scikit-learn")
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
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # 提取关键字段
                name = data.get("name", "Unknown")
                description = data.get("description", "")
                category = data.get("category", "Unknown")
                item_id = data.get("id", os.path.basename(file_path).replace(".json", ""))

                # 构造用于 Embedding 的文本内容
                text = f"Item: {name}\nCategory: {category}\nDescription: {description}"
                
                items.append({
                    "id": item_id,
                    "text": text,
                    "metadata": {
                        "name": name,
                        "category": category,
                        "description": description,
                        "path": file_path,
                        "raw_data": data # 保存原始数据以便使用
                    }
                })
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

        print(f"Generating embeddings for {len(items)} items... (This happens locally on CPU)")
        
        texts = [item["text"] for item in items]
        embeddings = self.embedding_model.embed_documents(texts)
        embedding_matrix = np.array(embeddings)
        
        data = {
            "items": items,
            "embedding_matrix": embedding_matrix
        }
        
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with open(self.db_path, 'wb') as f:
            pickle.dump(data, f)
            
        print(f"Saved index to {self.db_path}")

    def search(self, query: str, k: int = 3) -> List[Dict]:
        """搜索物品。"""
        if not os.path.exists(self.db_path):
            print(f"Index not found at {self.db_path}. Please build it first.")
            return []

        self._init_model()

        with open(self.db_path, 'rb') as f:
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
            results.append({
                "score": float(score),
                **item # 展开 item，包含 id, text, metadata
            })
            
        return results

# 为了方便直接调用，提供一个单例或辅助函数
def rebuild_vector_db(item_dir: str = "./data/item", db_path: str = "./data/simple_vector_store.pkl"):
    store = SimpleVectorStore(db_path=db_path)
    store.build_index(item_data_dir=item_dir)

def search_similar_items(query: str, k: int = 3, db_path: str = "./data/simple_vector_store.pkl") -> List[Dict]:
    store = SimpleVectorStore(db_path=db_path)
    return store.search(query, k=k)

if __name__ == "__main__":
    # 测试代码
    rebuild_vector_db()
    results = search_similar_items("something weapon")
    for res in results:
        print(f"[{res['score']:.4f}] {res['metadata']['name']}")
