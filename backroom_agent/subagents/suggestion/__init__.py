from backroom_agent.utils.node_annotation import get_node_annotation

from .graph import suggestion_agent
from .nodes import generate_suggestions_node

SUGGESTION_NODES = {"generate_suggestions": generate_suggestions_node}

SUGGESTION_LLM_NODES = {
    nid
    for nid, fn in SUGGESTION_NODES.items()
    if (ann := get_node_annotation(fn)) and ann.kind == "llm"
}

__all__ = ["suggestion_agent", "SUGGESTION_NODES", "SUGGESTION_LLM_NODES"]
