import glob
import json
import os

from graphviz import Digraph

from backroom_agent.utils.common import get_project_root


def sanitize_id(name):
    """Sanitize node name for Mermaid ID."""
    if not name:
        return "Unknown"
    # Replace chars that break mermaid
    safe = (
        name.replace(" ", "_")
        .replace("-", "_")
        .replace(".", "")
        .replace("(", "")
        .replace(")", "")
        .replace("'", "")
    )
    return safe


def generate_level_graph():
    root = get_project_root()
    level_dir = os.path.join(root, "data/level")
    files = glob.glob(os.path.join(level_dir, "*.json"))

    nodes = set()
    edges = []

    print(f"Found {len(files)} level files.")

    for fpath in files:
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Error reading {fpath}: {e}")
            continue

        source = data.get("level_id")
        title = data.get("title")

        if not source:
            print(f"Skipping {fpath}: Missing level_id")
            continue

        nodes.add((source, title))

        transitions = data.get("transitions", {})
        exits = transitions.get("exits", [])

        for exit_info in exits:
            target = exit_info.get("next")
            if target:
                # We add the target to nodes as well so it appears even if we don't have a file for it
                # But we don't have a title for it yet

                # Check if target is already in nodes (to avoid adding it without title if we have it later)
                # Actually, simpler to just collect edges and then build graph
                edges.append(
                    {
                        "from": source,
                        "to": target,
                        "method": exit_info.get("method", "Unknown method"),
                    }
                )

    # Generate Graphviz Digraph
    dot = Digraph("Level Map", comment="The Backrooms Level Map", format="png")
    dot.attr(rankdir="TB")  # Top to Bottom flow
    dot.attr("node", shape="rect", fontname="Helvetica")
    dot.attr("edge", fontname="Helvetica", fontsize="10")

    # Add nodes (Explored - Green)
    known_ids = {n[0] for n in nodes}
    for level_id, level_title in nodes:
        safe_id = sanitize_id(level_id)
        # Standard label
        label = f"{level_id}"
        if level_title:
            label += f"\\n({level_title})"

        # Explored: PaleGreen background, solid border
        dot.node(safe_id, label=label, style="filled", fillcolor="#98FB98")

    # Add edges
    # We first group edges by source to count them
    edges_by_source = {}
    for edge in edges:
        src = edge["from"]
        if src not in edges_by_source:
            edges_by_source[src] = []
        edges_by_source[src].append(edge)

    for src, src_edges in edges_by_source.items():
        safe_src = sanitize_id(src)

        # Check if we need to split
        if len(src_edges) > 5:
            # Main connections (first 5)
            main_edges = src_edges[:5]
            other_edges = src_edges[5:]

            # Draw main edges
            for edge in main_edges:
                dst = edge["to"]
                method = edge["method"]
                safe_dst = sanitize_id(dst)

                if dst not in known_ids:
                    # Unexplored: LightGrey background, dashed border
                    dot.node(
                        safe_dst,
                        label=dst,
                        style="filled,dashed",
                        fillcolor="lightgrey",
                    )
                    known_ids.add(dst)

                short_method = method[:20] + "..." if len(method) > 20 else method
                dot.edge(safe_src, safe_dst, label=short_method)

            # Create a summary node for the rest
            summary_node_id = f"{safe_src}_more"
            summary_label = f"+{len(other_edges)} more exits"
            dot.node(
                summary_node_id, label=summary_label, shape="ellipse", style="dashed"
            )
            dot.edge(safe_src, summary_node_id, style="dashed", arrowh="none")

            # Connect the summary node to the other destinations with dashed lines
            for edge in other_edges:
                dst = edge["to"]
                method = edge["method"]
                safe_dst = sanitize_id(dst)

                if dst not in known_ids:
                    # Unexplored: LightGrey background, dashed border
                    dot.node(
                        safe_dst,
                        label=dst,
                        style="filled,dashed",
                        fillcolor="lightgrey",
                    )
                    known_ids.add(dst)

                short_method = method[:20] + "..." if len(method) > 20 else method
                dot.edge(
                    summary_node_id,
                    safe_dst,
                    label=short_method,
                    style="dashed",
                    color="grey",
                )

        else:
            # Draw all edges normally
            for edge in src_edges:
                dst = edge["to"]
                method = edge["method"]

                safe_dst = sanitize_id(dst)

                # Add implicit nodes
                if dst not in known_ids:
                    # Unexplored: LightGrey background, dashed border
                    dot.node(
                        safe_dst,
                        label=dst,
                        style="filled,dashed",
                        fillcolor="lightgrey",
                    )
                    known_ids.add(dst)

                short_method = method[:20] + "..." if len(method) > 20 else method
                dot.edge(safe_src, safe_dst, label=short_method)

    # Ensure tmp directory exists
    tmp_dir = os.path.join(root, "tmp")
    os.makedirs(tmp_dir, exist_ok=True)

    output_filename = os.path.join(tmp_dir, "level_map")  # graphviz appends .png

    try:
        output_path = dot.render(output_filename, cleanup=True)
        print(f"Graph generated at: {output_path}")
    except Exception as e:
        print(f"Failed to render graph via Graphviz: {e}")
        print(
            "Ensure 'dot' is installed on your system (e.g. 'brew install graphviz')."
        )


if __name__ == "__main__":
    generate_level_graph()
