import json
import logging
import os

from backroom_agent.utils.common import get_project_root

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
    extracted_links = state.get("extracted_links", [])
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
        data["links"] = extracted_links

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
        # Optimized: We explicitly skipped real-time vector store updates in update_level_json_node.
        # Vector store updates are now handled in post-processing/batch operations.
        # No logging needed here as we are doing nothing.

    except Exception as e:
        logs.append(f"Error updating JSON/Files: {str(e)}")

    return {"logs": logs}
