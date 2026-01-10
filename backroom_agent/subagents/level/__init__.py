from backroom_agent.utils.node_annotation import get_node_annotation

from .graph import level_agent
from .nodes import (check_completion_node, fetch_content_node,
                    filter_entities_node, filter_items_node,
                    update_level_json_node)
from .nodes_llm import (extract_entities_node, extract_items_node,
                        generate_json_node)

LEVEL_NODES = {
    "fetch_content": fetch_content_node,
    "generate_json": generate_json_node,
    "extract_items": extract_items_node,
    "extract_entities": extract_entities_node,
    "filter_items": filter_items_node,
    "filter_entities": filter_entities_node,
    "check_completion": check_completion_node,
    "update_level_json": update_level_json_node,
}

LEVEL_LLM_NODES = {
    nid
    for nid, fn in LEVEL_NODES.items()
    if (ann := get_node_annotation(fn)) and ann.kind == "llm"
}

__all__ = ["level_agent", "LEVEL_NODES", "LEVEL_LLM_NODES"]
