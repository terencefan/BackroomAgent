import argparse
import os

from backroom_agent.utils.common import get_project_root
from backroom_agent.utils.vector_store import rebuild_vector_db


def rebuild_indices(backend="pickle"):
    root = get_project_root()
    item_root_dir = os.path.join(root, "data/item")
    entity_root_dir = os.path.join(root, "data/entity")
    vector_store_dir = os.path.join(root, "data/vector_store")

    os.makedirs(vector_store_dir, exist_ok=True)

    print(
        f"Rebuilding Item Vector Store at data/vector_store/item_vector_store.pkl (Backend: {backend})..."
    )
    rebuild_vector_db(
        item_dir=item_root_dir,
        db_path=os.path.join(vector_store_dir, "item_vector_store.pkl"),
        backend=backend,
    )

    print(
        f"Rebuilding Entity Vector Store at data/vector_store/entity_vector_store.pkl (Backend: {backend})..."
    )
    rebuild_vector_db(
        item_dir=entity_root_dir,
        db_path=os.path.join(vector_store_dir, "entity_vector_store.pkl"),
        backend=backend,
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--backend",
        default="pickle",
        choices=["pickle", "chroma"],
        help="Vector store backend to use",
    )
    args = parser.parse_args()

    rebuild_indices(backend=args.backend)
