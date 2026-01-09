from typing import Dict, List, Optional

from .chroma_store import ChromaVectorStore
# 使用相对导入，方便包内部重构
from .pickle_store import PickleVectorStore

# 默认使用 pickle (简单，无外部DB依赖)
# Change to "chroma" to use ChromaDB by default
bg_backend = "pickle"


class SimpleVectorStore(PickleVectorStore):
    """
    Deprecated: Warning wrapper for backward compatibility.
    Use PickleVectorStore directly or configure the backend.
    """

    pass


__all__ = [
    "SimpleVectorStore",
    "PickleVectorStore",
    "ChromaVectorStore",
    "rebuild_vector_db",
    "update_vector_db",
    "search_similar_items",
]


def _get_store(
    backend: str,
    db_path: str,
    provider: str,
    model_name: str,
    collection_name: str = "item_collection",
):
    """Factory to get the correct vector store instance."""
    if backend == "chroma":
        # For Chroma, db_path is treated as persist_directory
        # If the user passed a file path (ending in .pkl), strip it to get a dir
        if db_path.endswith(".pkl"):
            persist_dir = db_path.replace(".pkl", "_chroma_db")
            persist_dir = persist_dir.replace(
                "/vector_store/", "/vector_store/chroma/"
            )  # Organize better
        else:
            persist_dir = db_path

        return ChromaVectorStore(
            collection_name=collection_name,
            persist_directory=persist_dir,
            model_name=model_name,
            provider=provider,
        )
    else:
        # Default to Pickle
        return PickleVectorStore(
            db_path=db_path, provider=provider, model_name=model_name
        )


def rebuild_vector_db(
    item_dir: str = "./data/item",
    db_path: str = "./data/vector_store/item_vector_store.pkl",
    provider: str = "local",
    model_name: str = "all-MiniLM-L6-v2",
    backend: str = "pickle",  # "pickle" or "chroma"
):
    """
    Rebuilds the vector database from scratch using all items in data/item.
    """
    store = _get_store(backend, db_path, provider, model_name)
    store.build_index(item_data_dir=item_dir)


def update_vector_db(
    file_paths: List[str],
    db_path: str = "./data/vector_store/item_vector_store.pkl",
    provider: str = "local",
    model_name: str = "all-MiniLM-L6-v2",
    backend: str = "pickle",
):
    """
    Updates the vector database with specific files.
    """
    store = _get_store(backend, db_path, provider, model_name)
    store.update_index(file_paths)


def search_similar_items(
    query: str,
    k: int = 5,
    db_path: str = "./data/vector_store/item_vector_store.pkl",
    provider: str = "local",
    model_name: str = "all-MiniLM-L6-v2",
    backend: str = "pickle",
) -> List[Dict]:
    """
    Searches for items similar to the query.
    """
    store = _get_store(backend, db_path, provider, model_name)
    return store.search(query, k=k)
