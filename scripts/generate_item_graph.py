import json
import os

from backroom_agent.utils.analysis import get_all_level_references
from backroom_agent.utils.common import get_project_root
from backroom_agent.utils.visualization import (generate_bipartite_graph,
                                              generate_interactive_bipartite_graph)


def generate_graph():
    root = get_project_root()
    tmp_dir = os.path.join(root, "tmp")

    print("Analyzing item references...")
    refs = get_all_level_references()

    item_data = refs["items"]
    level_names = refs["level_names"]

    # Merge names
    all_names = {**item_data["names"], **level_names}

    print(f"Found {len(item_data['valid_ids'])} unique valid item IDs.")

    # Generate Graph
    print("Generating Item-Level Graph...")
    maps_dir = os.path.join(tmp_dir, "maps")
    os.makedirs(maps_dir, exist_ok=True)
    generate_bipartite_graph(
        item_data["map"],
        all_names,
        "Item Distribution Map",
        os.path.join(maps_dir, "item_level_map.png"),
    )

    print("Generating Interactive Item-Level Graph...")
    generate_interactive_bipartite_graph(
        item_data["map"],
        all_names,
        "Item Distribution Map",
        os.path.join(maps_dir, "item_level_map.html"),
    )

    # Save Valid Item IDs (Shared with clean_orphans if needed, though clean_orphans can re-scan)
    # To be safe and explicit, let's keep the valid_ids.json pattern or updated specific file
    valid_ids_path = os.path.join(tmp_dir, "valid_item_ids.json")
    with open(valid_ids_path, "w", encoding="utf-8") as f:
        json.dump(list(item_data["valid_ids"]), f, indent=2)
    print(f"Saved valid item IDs to {valid_ids_path}")


if __name__ == "__main__":
    generate_graph()
