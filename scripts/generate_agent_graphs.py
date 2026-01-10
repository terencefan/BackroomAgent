import os
import re
import sys

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from langchain_core.runnables.graph_mermaid import draw_mermaid_png

from backroom_agent.graph import graph as main_graph
from backroom_agent.nodes import LLM_NODE_IDS
from backroom_agent.subagents.level.graph import level_agent
from backroom_agent.subagents.level.nodes import (check_completion_node,
                                                  fetch_content_node,
                                                  filter_entities_node,
                                                  filter_items_node,
                                                  update_level_json_node)
from backroom_agent.subagents.level.nodes_llm import (extract_entities_node,
                                                      extract_items_node,
                                                      generate_json_node)
from backroom_agent.subagents.suggestion.graph import suggestion_agent
from backroom_agent.subagents.suggestion.nodes import generate_suggestions_node
from backroom_agent.utils.node_annotation import is_llm_node


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


def generate_combined_graph(tmp_dir, main_llm_nodes, suggestion_llm_nodes):
    print("Generating Combined Agent Graph...")

    main_src = main_graph.get_graph().draw_mermaid()
    sub_src = suggestion_agent.get_graph().draw_mermaid()

    sub_edges, sub_entry, sub_exit = parse_graph_structure(sub_src)

    prefix = "sg_"
    sub_entry = f"{prefix}{sub_entry}" if sub_entry else None
    sub_exit = f"{prefix}{sub_exit}" if sub_exit else None

    prefixed_sub_edges = []
    for edge in sub_edges:
        parts = re.split(r"(\s*(?:--|==|-[.]-)+>\s*)", edge)
        if len(parts) >= 3:
            u = parts[0]
            arrow = parts[1]
            v = parts[2]
            prefixed_sub_edges.append(f"{prefix}{u}{arrow}{prefix}{v}")

    new_lines = ["graph TD;"]

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

            if u == "suggest":
                u = sub_exit if sub_exit else u
            if v == "suggest":
                v = sub_entry if sub_entry else v

            if u and v:
                new_lines.append(f"    {u} {arrow} {v};")
        else:
            if "suggest" in line:
                continue
            new_lines.append(f"    {line};")

    new_lines.append("    subgraph Suggestion_Agent")
    if prefixed_sub_edges:
        for edge in prefixed_sub_edges:
            new_lines.append(f"        {edge};")
    else:
        if sub_entry and sub_entry == sub_exit:
            new_lines.append(f"        {sub_entry};")
    new_lines.append("    end")

    combined_mermaid = "\n".join(new_lines)

    combined_llm_nodes = set(main_llm_nodes)
    combined_llm_nodes.update({f"sg_{nid}" for nid in suggestion_llm_nodes})

    arch_dir = os.path.join(tmp_dir, "architecture")
    os.makedirs(arch_dir, exist_ok=True)

    style_and_save_graph(
        None,
        os.path.join(arch_dir, "combined_agent_graph.png"),
        combined_llm_nodes,
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
    level_nodes = {
        "fetch_content": fetch_content_node,
        "generate_json": generate_json_node,
        "extract_items": extract_items_node,
        "extract_entities": extract_entities_node,
        "filter_items": filter_items_node,
        "filter_entities": filter_entities_node,
        "check_completion": check_completion_node,
        "update_level_json": update_level_json_node,
    }
    level_llm_nodes = {
        node_id for node_id, fn in level_nodes.items() if is_llm_node(fn)
    }
    style_and_save_graph(
        level_agent, os.path.join(arch_dir, "level_agent_graph.png"), level_llm_nodes
    )

    suggestion_nodes = {"generate_suggestions": generate_suggestions_node}
    suggestion_llm_nodes = {
        node_id for node_id, fn in suggestion_nodes.items() if is_llm_node(fn)
    }

    generate_combined_graph(tmp_dir, main_llm_nodes, suggestion_llm_nodes)


if __name__ == "__main__":
    generate_graphs()
