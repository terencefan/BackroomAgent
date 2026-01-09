import glob
import json
import os

from backroom_agent.utils.analysis import get_all_level_references
from backroom_agent.utils.common import get_project_root


def clean_orphans():
    root = get_project_root()
    item_root_dir = os.path.join(root, "data/item")
    entity_root_dir = os.path.join(root, "data/entity")

    print("Analyzing references to find valid IDs...")
    refs = get_all_level_references()
    valid_item_ids = refs["items"]["valid_ids"]
    valid_entity_ids = refs["entities"]["valid_ids"]

    print(
        f"Found {len(valid_item_ids)} valid item IDs and {len(valid_entity_ids)} valid entity IDs."
    )

    # 2. Cleanup Items
    item_files = glob.glob(os.path.join(item_root_dir, "**", "*.json"), recursive=True)
    deleted_items = 0
    for file_path in item_files:
        filename = os.path.basename(file_path)
        item_id = os.path.splitext(filename)[0]

        # Skip if it's a directory
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


if __name__ == "__main__":
    clean_orphans()
