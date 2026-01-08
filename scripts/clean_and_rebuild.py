import glob
import json
import os
from collections import defaultdict

import matplotlib
import networkx as nx

matplotlib.use("Agg")  # Use non-interactive backend
import matplotlib.pyplot as plt

from backroom_agent.utils.common import get_project_root
from backroom_agent.utils.vector_store import rebuild_vector_db

# Configure Matplotlib to use Chinese fonts
plt.rcParams["font.sans-serif"] = [
    "Arial Unicode MS",
    "PingFang SC",
    "Heiti TC",
    "sans-serif",
]
plt.rcParams["axes.unicode_minus"] = False


def generate_graph(data_map, id_to_name, title, output_path):
    """
    Generates a bipartite graph from a mapping (Item/Entity -> [Levels]).
    """
    G = nx.Graph()

    # Add nodes and edges
    items = list(data_map.keys())
    all_levels = set()

    for item, levels in data_map.items():
        G.add_node(item, bipartite=0, node_type="object")
        for level in levels:
            all_levels.add(level)
            G.add_edge(item, level)

    for level in all_levels:
        G.add_node(level, bipartite=1, node_type="level")

    # Layout
    pos = nx.spring_layout(G, k=0.5, iterations=50)

    plt.figure(figsize=(15, 10))

    # Draw Levels
    level_nodes = [n for n, d in G.nodes(data=True) if d["node_type"] == "level"]
    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=level_nodes,
        node_color="lightcoral",
        node_size=1500,
        label="Levels",
    )

    # Draw Items/Entities
    obj_nodes = [n for n, d in G.nodes(data=True) if d["node_type"] == "object"]
    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=obj_nodes,
        node_color="skyblue",
        node_size=800,
        label="Items/Entities",
    )

    # Draw Edges
    nx.draw_networkx_edges(G, pos, alpha=0.3)

    # Draw Labels
    labels = {}
    for n in G.nodes():
        if n in id_to_name:
            labels[n] = id_to_name[n]
        else:
            labels[n] = n

    nx.draw_networkx_labels(G, pos, labels, font_size=8, font_family="Arial Unicode MS")

    plt.title(title)
    plt.legend()
    plt.axis("off")

    plt.savefig(output_path, bbox_inches="tight", dpi=150)
    plt.close()
    print(f"Graph saved to {output_path}")


def clean_and_rebuild():
    root = get_project_root()
    level_dir = os.path.join(root, "data/level")
    item_root_dir = os.path.join(root, "data/item")
    entity_root_dir = os.path.join(root, "data/entity")
    vector_store_dir = os.path.join(root, "data/vector_store")
    tmp_dir = os.path.join(root, "tmp")

    # Ensure dirs exist
    os.makedirs(vector_store_dir, exist_ok=True)
    os.makedirs(tmp_dir, exist_ok=True)

    # 1. Collect Valid IDs from Levels
    valid_item_ids = set()
    valid_entity_ids = set()

    # Inverted Index: ID -> List[LevelID]
    item_to_levels = defaultdict(list)
    entity_to_levels = defaultdict(list)

    # ID -> Name Map
    item_id_to_name = {}
    entity_id_to_name = {}

    level_files = glob.glob(os.path.join(level_dir, "*.json"))
    print(f"Scanning {len(level_files)} level files for references...")

    for level_file in level_files:
        try:
            level_id = os.path.splitext(os.path.basename(level_file))[0]
            with open(level_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Items
            items = data.get("findable_items", [])
            for item in items:
                if "id" in item:
                    iid = item["id"]
                    name = item.get("name", iid)
                    valid_item_ids.add(iid)
                    item_to_levels[iid].append(level_id)
                    item_id_to_name[iid] = name

            # Entities
            entities = data.get("entities", [])
            for entity in entities:
                if "id" in entity:
                    eid = entity["id"]
                    name = entity.get("name", eid)
                    valid_entity_ids.add(eid)
                    entity_to_levels[eid].append(level_id)
                    entity_id_to_name[eid] = name

        except Exception as e:
            print(f"Error reading {level_file}: {e}")

    print(f"Found {len(valid_item_ids)} unique valid item IDs.")
    print(f"Found {len(valid_entity_ids)} unique valid entity IDs.")

    # Generate Graphs
    print("Generating Item-Level Graph...")
    generate_graph(
        item_to_levels,
        item_id_to_name,
        "Item Distribution Map",
        os.path.join(tmp_dir, "item_level_map.png"),
    )

    print("Generating Entity-Level Graph...")
    generate_graph(
        entity_to_levels,
        entity_id_to_name,
        "Entity Distribution Map",
        os.path.join(tmp_dir, "entity_level_map.png"),
    )

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

    old_entity_store = os.path.join(
        root, "data/entity_vector_store.pkl"
    )  # Previous location
    if os.path.exists(old_entity_store):
        print(f"Removing old entity store: {old_entity_store}")
        os.remove(old_entity_store)

    # 5. Rebuild Vector Databases
    print("Rebuilding Item Vector Store at data/vector_store/item_vector_store.pkl...")
    rebuild_vector_db(
        item_dir=item_root_dir,
        db_path=os.path.join(vector_store_dir, "item_vector_store.pkl"),
    )

    print(
        "Rebuilding Entity Vector Store at data/vector_store/entity_vector_store.pkl..."
    )
    rebuild_vector_db(
        item_dir=entity_root_dir,
        db_path=os.path.join(vector_store_dir, "entity_vector_store.pkl"),
    )

    print("Clean and Rebuild Complete.")


if __name__ == "__main__":
    clean_and_rebuild()
