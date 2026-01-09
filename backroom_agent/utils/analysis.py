import glob
import json
import os
from collections import defaultdict
from typing import Any, Dict, List, Set, TypedDict, cast

from .common import get_project_root


class CategoryData(TypedDict):
    valid_ids: Set[str]
    map: Dict[str, List[str]]
    names: Dict[str, str]


class AnalysisResult(TypedDict):
    items: CategoryData
    entities: CategoryData
    level_names: Dict[str, str]


def get_all_level_references() -> AnalysisResult:
    """
    Scans all level files and returns valid IDs and mappings.
    Returns:
        AnalysisResult
    """
    root = get_project_root()
    level_dir = os.path.join(root, "data/level")
    item_dir = os.path.join(root, "data/item")
    entity_dir = os.path.join(root, "data/entity")

    # Results
    res: AnalysisResult = {
        "items": {"valid_ids": set(), "map": defaultdict(list), "names": {}},
        "entities": {"valid_ids": set(), "map": defaultdict(list), "names": {}},
        "level_names": {},
    }

    # 1. Build Name -> ID Maps from data/item and data/entity
    item_name_to_id: Dict[str, str] = {}
    entity_name_to_id: Dict[str, str] = {}

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
                raw_entities = data.get("entities_list", data.get("entities", []))

                # Check if it's a list of dicts
                if isinstance(raw_entities, list):
                    matches = cast(List[Any], raw_entities)
                    if len(matches) > 0 and isinstance(matches[0], dict):
                        # Explicit cast for type safety
                        typed_entities = cast(List[Dict[str, Any]], matches)
                        for entity in typed_entities:
                            if "id" in entity:
                                eid = entity["id"]
                                name = entity.get("name", eid)
                                res["entities"]["valid_ids"].add(eid)
                                res["entities"]["map"][eid].append(level_id)
                                res["entities"]["names"][eid] = name

        except Exception as e:
            print(f"Error reading {level_file}: {e}")

    return res
