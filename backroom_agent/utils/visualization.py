import math
import os

import matplotlib
import matplotlib.pyplot as plt
import networkx as nx

# Use non-interactive backend
matplotlib.use("Agg")

# Configure Matplotlib to use Chinese fonts
plt.rcParams["font.sans-serif"] = [
    "Arial Unicode MS",
    "PingFang SC",
    "Heiti TC",
    "sans-serif",
]
plt.rcParams["axes.unicode_minus"] = False


def generate_bipartite_graph(data_map, id_to_name, title, output_path):
    """
    Generates a bipartite graph connecting Levels (Outer Ring) to Items/Entities (Center).
    Items/Entities are colored based on their degree (connectivity heat).
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

    # Separation of nodes
    level_nodes = [n for n, d in G.nodes(data=True) if d["node_type"] == "level"]
    obj_nodes = [n for n, d in G.nodes(data=True) if d["node_type"] == "object"]

    # --- Layout Strategy: Fixed Circle for Levels, Spring for Objects ---
    pos = {}
    # Place levels in a large circle
    level_radius = 1.0
    if level_nodes:
        # Sort levels for consistent visual order (optional)
        level_nodes.sort()
        angle_step = 2 * math.pi / len(level_nodes)
        for i, node in enumerate(level_nodes):
            angle = i * angle_step
            pos[node] = (level_radius * math.cos(angle), level_radius * math.sin(angle))

    # Run spring layout, fixing the level nodes, allowing objects to settle in the center
    # k controls node spacing. Increasing k helps reduce overlap.
    # We use a larger k here (0.3) compared to default.
    pos = nx.spring_layout(
        G, pos=pos, fixed=level_nodes, k=0.3, iterations=200, scale=0.8
    )

    plt.figure(figsize=(20, 16))  # Larger canvas for star/wheel layout

    # --- Draw Levels (Outer Ring) ---
    nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=level_nodes,
        node_color="#E0E0E0",  # Light gray neutral
        node_size=2500,
        edgecolors="gray",  # Border
        label="Levels",
    )

    # --- Draw Objects (Center Heatmap) ---
    # Calculate degrees for heat mapping
    obj_degrees = [G.degree(n) for n in obj_nodes]

    # Scale node size by degree (min 500, max 2000)
    # Avoid division by zero if all degrees are same or empty
    max_deg = 1
    if obj_degrees:
        max_deg = max(obj_degrees)
        # Simple linear scaling
        obj_sizes = [500 + (d / max(1, max_deg)) * 1500 for d in obj_degrees]
    else:
        obj_sizes = 500

    nodes = nx.draw_networkx_nodes(
        G,
        pos,
        nodelist=obj_nodes,
        node_color=obj_degrees,
        cmap=plt.cm.YlOrRd,  # Yellow to Red heat map
        node_size=obj_sizes,
        edgecolors="black",  # Border for contrast
        linewidths=0.5,
        label="Items/Entities",
        alpha=0.9,
    )

    # --- Draw Edges ---
    # Use curve edges or straight? Straight is standard for spring.
    nx.draw_networkx_edges(G, pos, alpha=0.15, edge_color="gray")

    # --- Draw Labels with Adaptive Color ---
    labels = {}
    for n in G.nodes():
        if n in id_to_name:
            labels[n] = id_to_name[n]
        else:
            labels[n] = n

    # 1. Level Labels (Always Black)
    nx.draw_networkx_labels(
        G,
        pos,
        labels={n: labels[n] for n in level_nodes},
        font_size=9,
        font_family="Arial Unicode MS",
        font_weight="bold",
        font_color="black",
    )

    # 2. Object Labels (Adaptive)
    # Split objects into dark (High degree) and light (Low degree) for text contrast
    dark_text_nodes = []
    light_text_nodes = []

    threshold = (
        0.5 * max_deg
    )  # Threshold for switching text color (roughly middle of heatmap)

    for n in obj_nodes:
        deg = G.degree(n)
        if deg > threshold:
            light_text_nodes.append(n)  # Dark background -> Light text
        else:
            dark_text_nodes.append(n)  # Light background -> Dark text

    if dark_text_nodes:
        nx.draw_networkx_labels(
            G,
            pos,
            labels={n: labels[n] for n in dark_text_nodes},
            font_size=8,
            font_family="Arial Unicode MS",
            font_color="black",
        )

    if light_text_nodes:
        nx.draw_networkx_labels(
            G,
            pos,
            labels={n: labels[n] for n in light_text_nodes},
            font_size=8,
            font_family="Arial Unicode MS",
            font_color="white",
            font_weight="bold",  # Make white text bold for better readability
        )

    # Add Colorbar for Heatmap
    if obj_nodes:
        cb = plt.colorbar(nodes, shrink=0.8)
        cb.set_label("Connectivity (Degree)")

    plt.title(title, fontsize=16)
    plt.axis("off")

    # Ensure directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    plt.savefig(output_path, bbox_inches="tight", dpi=150)
    plt.close()
    print(f"Graph saved to {output_path}")
