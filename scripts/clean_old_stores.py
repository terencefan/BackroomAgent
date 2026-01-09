import argparse
import os
import shutil

from backroom_agent.utils.common import get_project_root


def clean_stores(backend="pickle"):
    root = get_project_root()
    vector_store_dir = os.path.join(root, "data/vector_store")

    paths_to_remove = []

    if backend == "pickle":
        # Pickle Files
        paths_to_remove = [
            os.path.join(vector_store_dir, "item_vector_store.pkl"),
            os.path.join(vector_store_dir, "entity_vector_store.pkl"),
            # Legacy paths
            os.path.join(root, "data/simple_vector_store.pkl"),
            os.path.join(root, "data/entity_vector_store.pkl"),
        ]
    elif backend == "chroma":
        # Chroma Directories
        paths_to_remove = [
            os.path.join(vector_store_dir, "item_vector_store_chroma_db"),
            os.path.join(vector_store_dir, "entity_vector_store_chroma_db"),
        ]

    print(f"Cleaning {backend} stores...")
    for path in paths_to_remove:
        if os.path.exists(path):
            print(f"Removing: {path}")
            if os.path.isfile(path):
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
        else:
            # print(f"Not found: {path}")
            pass


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--backend",
        default="pickle",
        choices=["pickle", "chroma"],
        help="Vector store backend to clean",
    )
    args = parser.parse_args()

    clean_stores(backend=args.backend)
