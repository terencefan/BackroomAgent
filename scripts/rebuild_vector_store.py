#!/usr/bin/env python3
import os
import sys

# Ensure correct path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backroom_agent.utils.common import get_project_root
from backroom_agent.utils.vector_store import rebuild_vector_db

def main():
    root = get_project_root()
    
    # Items
    item_dir = os.path.join(root, "data/item")
    item_db_path = os.path.join(root, "data/vector_store/item_vector_store.pkl")
    print(f"Rebuilding Item Vector Store from {item_dir}...")
    rebuild_vector_db(item_dir=item_dir, db_path=item_db_path)
    print("Item Vector Store rebuilt.")
    
    # Entities
    entity_dir = os.path.join(root, "data/entity")
    entity_db_path = os.path.join(root, "data/vector_store/entity_vector_store.pkl")
    print(f"Rebuilding Entity Vector Store from {entity_dir}...")
    rebuild_vector_db(item_dir=entity_dir, db_path=entity_db_path)
    print("Entity Vector Store rebuilt.")

if __name__ == "__main__":
    main()
