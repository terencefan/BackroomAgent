import glob
import json
import os
from collections import defaultdict
from typing import Dict, List, Set

from .common import get_project_root


def get_all_level_references() -> Dict[str, Dict]:
    """
    Scans all level files and returns valid IDs and mappings.
    Returns:
        {
            "items": {"valid_ids": Set[str], "map": Dict[str, List[str]], "names": Dict[str, str]},
            "entities": {"valid_ids": Set[str], "map": Dict[str, List[str]], "names": Dict[str, str]}
        }
    """
    root = get_project_root()
    level_dir = os.path.join(root, "data/level")
    item_dir = os.path.join(root, "data/item")
    entity_dir = os.path.join(root, "data/entity")

    # Results
    res = {
        "items": {"valid_ids": set(), "map": defaultdict(list), "names": {}},
        "entities": {"valid_ids": set(), "map": defaultdict(list), "names": {}},
        "level_names": {},
    }

    # 1. Build Name -> ID Maps from data/item and data/entity
    item_name_to_id = {}
    entity_name_to_id = {}

    # Scan Items (Recursive)
    item_files = glob.glob(os.path.join(item_dir, "**/*.json"), recursive=True)
    for fpath in item_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                d = json.load(f)
                if "name" in d and "id" in d:
                    item_name_to_id[d["name"]] = d["id"]
        except Exception:
            pass

    # Scan Entities (Flat)
    entity_files = glob.glob(os.path.join(entity_dir, "*.json"))
    for fpath in entity_files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                d = json.load(f)
                if "name" in d and "id" in d:
                    entity_name_to_id[d["name"]] = d["id"]
        except Exception:
            pass

    level_files = glob.glob(os.path.join(level_dir, "*.json"))

    for level_file in level_files:
        try:
            level_id = os.path.splitext(os.path.basename(level_file))[0]
            with open(level_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Level Title
            # Format: "Level X\nTitle"
            raw_id = data.get("level_id", level_id)
            title = data.get("title", "")
            if title:
                display_name = f"{raw_id}\n{title}"
            else:
                display_name = raw_id

            res["level_names"][level_id] = display_name

            # Items (New Format - Strings)
            item_names = data.get("items", [])
            for name in item_names:
                iid = item_name_to_id.get(name)
                if iid:
                    res["items"]["valid_ids"].add(iid)
                    res["items"]["map"][iid].append(level_id)
                    res["items"]["names"][iid] = name
            
            # Items (Old Format - Objects)
            if not item_names:
                items = data.get("findable_items", [])
                for item in items:
                    if "id" in item:
                        iid = item["id"]
                        # Use name for display if available, fallback to ID
                        name = item.get("name", iid)
                        res["items"]["valid_ids"].add(iid)
                        res["items"]["map"][iid].append(level_id)
                        res["items"]["names"][iid] = name

            # Entities (New Format - Strings)
            entity_names = data.get("entities", [])
            for name in entity_names:
                eid = entity_name_to_id.get(name)
                if eid:
                    res["entities"]["valid_ids"].add(eid)
                    res["entities"]["map"][eid].append(level_id)
                    res["entities"]["names"][eid] = name

            # Entities (Old Format - Objects)
            if not entity_names:
                entities = data.get("entities_list", data.get("entities", [])) # Handle potential key confusion if objects were under 'entities' before
                # Check if first element is object
                if isinstance(entities, list) and len(entities) > 0 and isinstance(entities[0], dict):
                    for entity in entities:
                        if "id" in entity:
                            eid = entity["id"]
                            name = entity.get("name", eid)
                            res["entities"]["valid_ids"].add(eid)
                            res["entities"]["map"][eid].append(level_id)
                            res["entities"]["names"][eid] = name

        except Exception as e:
            print(f"Error reading {level_file}: {e}")

    return res
