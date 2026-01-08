import os
import json
import glob
import shutil
from backroom_agent.utils.common import get_project_root
from backroom_agent.utils.vector_store import rebuild_vector_db

def clean_and_rebuild():
    root = get_project_root()
    level_dir = os.path.join(root, "data/level")
    item_root_dir = os.path.join(root, "data/item")
    entity_root_dir = os.path.join(root, "data/entity")
    vector_store_dir = os.path.join(root, "data/vector_store")
    
    # Ensure vector store dir exists
    os.makedirs(vector_store_dir, exist_ok=True)

    # 1. Collect Valid IDs from Levels
    valid_item_ids = set()
    valid_entity_ids = set()
    
    level_files = glob.glob(os.path.join(level_dir, "*.json"))
    print(f"Scanning {len(level_files)} level files for references...")
    
    for level_file in level_files:
        try:
            with open(level_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            # Items
            items = data.get("findable_items", [])
            for item in items:
                if "id" in item:
                    valid_item_ids.add(item["id"])
            
            # Entities
            entities = data.get("entities", [])
            for entity in entities:
                if "id" in entity:
                    valid_entity_ids.add(entity["id"])
                    
        except Exception as e:
            print(f"Error reading {level_file}: {e}")

    print(f"Found {len(valid_item_ids)} unique valid item IDs.")
    print(f"Found {len(valid_entity_ids)} unique valid entity IDs.")

    # 2. Cleanup Items
    item_files = glob.glob(os.path.join(item_root_dir, "**", "*.json"), recursive=True)
    deleted_items = 0
    for file_path in item_files:
        filename = os.path.basename(file_path)
        item_id = os.path.splitext(filename)[0]
        
        # Skip if it's a directory (glob shouldn't return dirs with *.json but just in case)
        if not os.path.isfile(file_path):
            continue
            
        if item_id not in valid_item_ids:
            print(f"Deleting orphan item: {file_path}")
            os.remove(file_path)
            deleted_items += 1
            
    # Cleanup empty directories in item/
    for dirpath, dirnames, files in os.walk(item_root_dir, topdown=False):
        if not files and not dirnames and dirpath != item_root_dir:
            os.rmdir(dirpath)
            
    print(f"Deleted {deleted_items} orphan item files.")

    # 3. Cleanup Entities
    entity_files = glob.glob(os.path.join(entity_root_dir, "*.json"))
    deleted_entities = 0
    for file_path in entity_files:
        filename = os.path.basename(file_path)
        entity_id = os.path.splitext(filename)[0]
        
        if entity_id not in valid_entity_ids:
            print(f"Deleting orphan entity: {file_path}")
            os.remove(file_path)
            deleted_entities += 1
            
    print(f"Deleted {deleted_entities} orphan entity files.")

    # 4. Remove old vector stores
    old_store = os.path.join(root, "data/simple_vector_store.pkl")
    if os.path.exists(old_store):
        print(f"Removing old vector store: {old_store}")
        os.remove(old_store)
        
    old_entity_store = os.path.join(root, "data/entity_vector_store.pkl") # Previous location
    if os.path.exists(old_entity_store):
        print(f"Removing old entity store: {old_entity_store}")
        os.remove(old_entity_store)

    # 5. Rebuild Vector Databases
    print("Rebuilding Item Vector Store at data/vector_store/item_vector_store.pkl...")
    rebuild_vector_db(
        item_dir=item_root_dir, 
        db_path=os.path.join(vector_store_dir, "item_vector_store.pkl")
    )
    
    print("Rebuilding Entity Vector Store at data/vector_store/entity_vector_store.pkl...")
    rebuild_vector_db(
        item_dir=entity_root_dir, 
        db_path=os.path.join(vector_store_dir, "entity_vector_store.pkl")
    )
    
    print("Clean and Rebuild Complete.")

if __name__ == "__main__":
    clean_and_rebuild()
