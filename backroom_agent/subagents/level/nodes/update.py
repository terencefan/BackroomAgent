import json
import logging
import os

from backroom_agent.utils.common import get_project_root
from backroom_agent.utils.vector_store import (rebuild_vector_db,
                                               update_vector_db)

from ..state import LevelAgentState

logger = logging.getLogger(__name__)


def check_completion_node(state: LevelAgentState):
    """
    Dummy/Barrier node to synchronize execution.
    It doesn't change state, just passes through.
    """
    return {}


def update_level_json_node(state: LevelAgentState):
    """
    Updates the Level JSON with the extracted and filtered items AND entities.
    """
    level_name = state.get("level_name")
    final_items = state.get("final_items", [])
    final_entities = state.get("final_entities", [])
    logs = state.get("logs", [])

    if not level_name:
        return {"logs": logs}

    root = get_project_root()
    json_path = os.path.join(root, "data/level", f"{level_name}.json")

    if not os.path.exists(json_path):
        logs.append(f"Warning: JSON file {json_path} not found. Cannot update items.")
        return {"logs": logs}

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        data["findable_items"] = final_items
        data["entities"] = final_entities

        # Remove old key if it exists to keep it clean
        if "items" in data:
            del data["items"]

        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logs.append(f"Updated level JSON: {json_path}")

        # --- Save Individual Item Files ---
        item_base_dir = os.path.join(root, "data/item")
        saved_items_count = 0
        saved_item_paths = []
        for item in final_items:
            try:
                cat = item.get("category", "Uncategorized")
                iid = item.get("id", "unknown")
                item_dir = os.path.join(item_base_dir, cat)
                os.makedirs(item_dir, exist_ok=True)

                item_path = os.path.join(item_dir, f"{iid}.json")
                with open(item_path, "w", encoding="utf-8") as f:
                    json.dump(item, f, ensure_ascii=False, indent=2)
                saved_items_count += 1
                saved_item_paths.append(item_path)
            except Exception as e:
                logs.append(f"Error saving item {item.get('name')}: {e}")

        # --- Save Individual Entity Files ---
        entity_base_dir = os.path.join(root, "data/entity")
        saved_entities_count = 0
        saved_entity_paths = []
        for entity in final_entities:
            try:
                # Entities generally don't have sub-categories like items, or rely on behavior
                # Simple structure: data/entity/{id}.json
                eid = entity.get("id", "unknown")
                os.makedirs(entity_base_dir, exist_ok=True)

                entity_path = os.path.join(entity_base_dir, f"{eid}.json")
                with open(entity_path, "w", encoding="utf-8") as f:
                    json.dump(entity, f, ensure_ascii=False, indent=2)
                saved_entities_count += 1
                saved_entity_paths.append(entity_path)
            except Exception as e:
                logs.append(f"Error saving entity {entity.get('name')}: {e}")

        logs.append(
            f"Saved {saved_items_count} item files and {saved_entities_count} entity files."
        )

        # --- Update Vector Stores ---
        try:
            # 1. Update Item Vector Store
            item_db_path = os.path.join(root, "data/vector_store/item_vector_store.pkl")
            if os.path.exists(item_db_path) and saved_item_paths:
                logs.append(
                    f"Updating Item Vector Store incrementally with {len(saved_item_paths)} items..."
                )
                update_vector_db(file_paths=saved_item_paths, db_path=item_db_path)
            else:
                logs.append("Rebuilding Item Vector Store (Full)...")
                rebuild_vector_db(item_dir=item_base_dir, db_path=item_db_path)

            # 2. Update Entity Vector Store
            entity_db_path = os.path.join(
                root, "data/vector_store/entity_vector_store.pkl"
            )
            if os.path.exists(entity_db_path) and saved_entity_paths:
                logs.append(
                    f"Updating Entity Vector Store incrementally with {len(saved_entity_paths)} entities..."
                )
                update_vector_db(file_paths=saved_entity_paths, db_path=entity_db_path)
            else:
                logs.append("Rebuilding Entity Vector Store (Full)...")
                rebuild_vector_db(item_dir=entity_base_dir, db_path=entity_db_path)

            logs.append("Vector stores updated successfully.")
        except Exception as e:
            logs.append(f"Error updating vector stores: {e}")

    except Exception as e:
        logs.append(f"Error updating JSON/Files: {str(e)}")

    return {"logs": logs}
