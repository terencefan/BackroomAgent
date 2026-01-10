import os
import re
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_core.runnables.graph_mermaid import draw_mermaid_png

from backroom_agent.graph import graph as main_graph
from backroom_agent.nodes import LLM_NODE_IDS
from backroom_agent.subagents.event import EVENT_LLM_NODES, event_agent
from backroom_agent.subagents.level import LEVEL_LLM_NODES, level_agent
from backroom_agent.subagents.suggestion import (SUGGESTION_LLM_NODES,
                                                 suggestion_agent)


def style_and_save_graph(graph_obj, output_path, llm_nodes, graph_mermaid_code=None):
    try:
        if graph_mermaid_code:
            raw_mermaid = graph_mermaid_code
        else:
            raw_mermaid = graph_obj.get_graph().draw_mermaid()

        # Clean Frontmatter
        if raw_mermaid.strip().startswith("---"):
            lines = raw_mermaid.splitlines()
            start_idx = 0
            for i, line in enumerate(lines):
                if line.strip().startswith("graph TD") or line.strip().startswith(
                    "graph LR"
                ):
                    start_idx = i
                    break
            raw_mermaid = "\n".join(lines[start_idx:])

        style_defs = (
            "\n"
            "classDef llm fill:#ffdfba,stroke:#333,stroke-width:2px,width:180px,min-width:180px;\n"
            "classDef normal fill:#baffc9,stroke:#333,stroke-width:2px,width:180px,min-width:180px;\n"
        )

        class_assignments = []

        if graph_obj and not graph_mermaid_code:
            nodes_to_style = graph_obj.get_graph().nodes
        else:
            # Fallback extraction from mermaid text
            found_ids = set(re.findall(r"([a-zA-Z0-9_]+)", raw_mermaid))
            keywords = {
                "graph",
                "TD",
                "subgraph",
                "end",
                "classDef",
                "style",
                "fill",
                "stroke",
                "class",
                "p",
                "div",
                "br",
            }
            nodes_to_style = {
                nid
                for nid in found_ids
                if nid not in keywords
                and not nid.startswith("fill")
                and not nid.startswith("stroke")
            }

        for node_id in nodes_to_style:
            if node_id.startswith("__"):
                continue

            base_id = node_id.replace("sg_", "")

            if node_id in llm_nodes or base_id in llm_nodes:
                class_assignments.append(f"class {node_id} llm;")
            else:
                class_assignments.append(f"class {node_id} normal;")

        final_mermaid = raw_mermaid + style_defs + "\n".join(class_assignments)

        png_bytes = draw_mermaid_png(mermaid_syntax=final_mermaid)
        with open(output_path, "wb") as f:
            f.write(png_bytes)
        print(f"Saved to {output_path}")

    except Exception as e:
        print(f"Error generating graph for {output_path}: {e}")
        if graph_mermaid_code:
            with open(output_path + ".mmd", "w") as f:
                f.write(graph_mermaid_code)
            print(f"Dumped faulty mermaid code to {output_path}.mmd")


def extract_body_lines(mermaid_src):
    lines = mermaid_src.splitlines()
    start_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("graph TD"):
            start_idx = i
            break

    if start_idx != -1:
        return lines[start_idx + 1 :]
    return lines


def parse_graph_structure(mermaid_src):
    lines = extract_body_lines(mermaid_src)
    edges = []
    entry = None
    exit_node = None

    edge_pattern = re.compile(
        r"([a-zA-Z0-9_]+)\s*((?:--|==|-[.]-)+>)\s*([a-zA-Z0-9_]+)"
    )

    for line in lines:
        line = line.strip().rstrip(";")
        if not line:
            continue

        match = edge_pattern.search(line)
        if match:
            u, arrow, v = match.groups()

            if u == "__start__":
                entry = v
                continue
            if v == "__end__":
                exit_node = u
                continue
            if u == "__end__" or v == "__start__":
                continue

            edges.append(line)

    return edges, entry, exit_node


def process_subgraph_lines(graph, prefix):
    src = graph.get_graph().draw_mermaid()
    edges, entry, exit_node = parse_graph_structure(src)

    prefixed_edges = []
    for edge in edges:
        parts = re.split(r"(\s*(?:--|==|-[.]-)+>\s*)", edge)
        if len(parts) >= 3:
            u = parts[0]
            arrow = parts[1]
            v = parts[2]
            prefixed_edges.append(f"{prefix}{u}{arrow}{prefix}{v}")

    prefixed_entry = f"{prefix}{entry}" if entry else None
    prefixed_exit = f"{prefix}{exit_node}" if exit_node else None

    return prefixed_edges, prefixed_entry, prefixed_exit


def generate_full_graph(tmp_dir):
    print("Generating Full Agent Graph (Combined)...")

    # Graph Definitions (Prefix -> (GraphObject, Title))
    subagents = {
        "sg_sugg_": (suggestion_agent, "Suggestion_Agent"),
        "sg_level_": (level_agent, "Level_Agent"),
        "sg_evt_": (event_agent, "Event_Agent"),
    }

    # Prepare Subagent Data
    subagent_data = {}
    all_llm_nodes = set(LLM_NODE_IDS)

    for prefix, (agent, title) in subagents.items():
        edges, entry, exit_n = process_subgraph_lines(agent, prefix)
        subagent_data[title] = {"edges": edges, "entry": entry, "exit": exit_n}

        # Collect LLM Nodes
        if title == "Suggestion_Agent":
            all_llm_nodes.update({f"{prefix}{nid}" for nid in SUGGESTION_LLM_NODES})
        elif title == "Level_Agent":
            all_llm_nodes.update({f"{prefix}{nid}" for nid in LEVEL_LLM_NODES})
        elif title == "Event_Agent":
            all_llm_nodes.update({f"{prefix}{nid}" for nid in EVENT_LLM_NODES})

    # Start Building Mermaid
    new_lines = ["graph TD;"]

    # Process Main Graph
    main_src = main_graph.get_graph().draw_mermaid()
    main_body = extract_body_lines(main_src)
    edge_pattern = re.compile(
        r"([a-zA-Z0-9_]+)\s*((?:--|==|-[.]-)+>)\s*([a-zA-Z0-9_]+)"
    )

    for line in main_body:
        line = line.strip().rstrip(";")
        if (
            not line
            or line.startswith("classDef")
            or line.startswith("%%")
            or line.startswith("class ")
        ):
            continue

        match = edge_pattern.search(line)
        if match:
            u, arrow, v = match.groups()

            # Link Suggestion Agent
            sugg_data = subagent_data["Suggestion_Agent"]
            if u == "suggestion_node" and sugg_data["exit"]:
                u = sugg_data["exit"]
            if v == "suggestion_node" and sugg_data["entry"]:
                v = sugg_data["entry"]

            # Note: Level and Event agents are standalone/tools, so no direct replacement in Main Graph edges.
            # We just display them alongside.

            if u and v:
                new_lines.append(f"    {u} {arrow} {v};")
        else:
            if "suggestion_node" in line:
                continue
            new_lines.append(f"    {line};")

    # Append Subgraphs
    for title, data in subagent_data.items():
        new_lines.append(f"    subgraph {title}")
        if data["edges"]:
            for edge in data["edges"]:
                new_lines.append(f"        {edge};")
        else:
            if data["entry"]:
                new_lines.append(f"        {data['entry']};")
        new_lines.append("    end")

    combined_mermaid = "\n".join(new_lines)
    arch_dir = os.path.join(tmp_dir, "architecture")
    os.makedirs(arch_dir, exist_ok=True)

    style_and_save_graph(
        None,
        os.path.join(arch_dir, "full_agent_graph.png"),
        all_llm_nodes,
        graph_mermaid_code=combined_mermaid,
    )


def generate_graphs():
    root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    tmp_dir = os.path.join(root, "tmp")
    arch_dir = os.path.join(tmp_dir, "architecture")
    os.makedirs(arch_dir, exist_ok=True)

    print("Generating Main Agent Graph...")
    main_llm_nodes = set(LLM_NODE_IDS)
    style_and_save_graph(
        main_graph, os.path.join(arch_dir, "agent_graph.png"), main_llm_nodes
    )

    print("Generating Level Agent Graph...")
    style_and_save_graph(
        level_agent, os.path.join(arch_dir, "level_agent_graph.png"), LEVEL_LLM_NODES
    )

    generate_full_graph(tmp_dir)


if __name__ == "__main__":
    generate_graphs()
