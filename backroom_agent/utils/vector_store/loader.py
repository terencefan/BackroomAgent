import glob
import json
import os
from typing import Dict, List, Optional


def load_item_from_file(file_path: str) -> Optional[Dict]:
    """Reads a single JSON file and returns a structured item dict."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # Extract fields
        name = data.get("name", "Unknown")
        description = data.get("description", "")
        category = data.get("category", None)
        behavior = data.get("behavior", None)  # For entities
        item_id = data.get("id", os.path.basename(file_path).replace(".json", ""))

        # Construct text for embedding
        if category:
            text = f"Item: {name}\nCategory: {category}\nDescription: {description}"
        elif behavior:
            text = f"Entity: {name}\nBehavior: {behavior}\nDescription: {description}"
        else:
            text = f"Object: {name}\nDescription: {description}"

        return {
            "id": item_id,
            "text": text,
            "metadata": {
                "name": name,
                "category": category,
                "behavior": behavior,
                "description": description,
                "path": file_path,
                "raw_data": data,  # Save raw data
            },
        }
    except Exception as e:
        print(f"Warning loading {file_path}: {e}")
        return None


def load_items_from_dir(item_data_dir: str = "./data/item") -> List[Dict]:
    """Traverses directory to load all items."""
    items = []
    # Recursive search
    search_pattern = os.path.join(item_data_dir, "**", "*.json")
    files = glob.glob(search_pattern, recursive=True)

    print(f"Found {len(files)} item files in {item_data_dir}.")

    for file_path in files:
        item = load_item_from_file(file_path)
        if item:
            items.append(item)

    return items
