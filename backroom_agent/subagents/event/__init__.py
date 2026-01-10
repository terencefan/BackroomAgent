from backroom_agent.utils.node_annotation import get_node_annotation

from .graph import event_agent
from .nodes import generate_event_node

EVENT_NODES = {"generate_event": generate_event_node}

EVENT_LLM_NODES = {
    nid
    for nid, fn in EVENT_NODES.items()
    if (ann := get_node_annotation(fn)) and ann.kind == "llm"
}

__all__ = ["event_agent", "EVENT_NODES", "EVENT_LLM_NODES"]
