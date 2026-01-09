import json
import os

from backroom_agent.utils.analysis import get_all_level_references
from backroom_agent.utils.common import get_project_root
from backroom_agent.utils.visualization import generate_bipartite_graph


def generate_graph():
    root = get_project_root()
    tmp_dir = os.path.join(root, "tmp")

    print("Analyzing entity references...")
    refs = get_all_level_references()

    entity_data = refs["entities"]
    level_names = refs["level_names"]

    # Merge names
    all_names = {**entity_data["names"], **level_names}

    print(f"Found {len(entity_data['valid_ids'])} unique valid entity IDs.")

    # Generate Graph
    print("Generating Entity-Level Graph...")
    generate_bipartite_graph(
        entity_data["map"],
        all_names,
        "Entity Distribution Map",
        os.path.join(tmp_dir, "entity_level_map.png"),
    )

    valid_ids_path = os.path.join(tmp_dir, "valid_entity_ids.json")
    with open(valid_ids_path, "w", encoding="utf-8") as f:
        json.dump(list(entity_data["valid_ids"]), f, indent=2)
    print(f"Saved valid entity IDs to {valid_ids_path}")


if __name__ == "__main__":
    generate_graph()
