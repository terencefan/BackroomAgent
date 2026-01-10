from backroom_agent.constants import NodeConstants
from backroom_agent.utils.node_annotation import (NodeAnnotation, NodeKind,
                                                  get_node_annotation)

from .dice import dice_node, route_check_dice
from .event import event_node
from .init import init_node
from .item_resolve import item_resolve_node
from .resolve import resolve_node
from .router import route_event, router_node
from .suggestion import suggestion_node
from .summary import summary_node

# Define Node Constants (Aliases to centralized constants)
NODE_ROUTER_NODE = NodeConstants.ROUTER_NODE
NODE_INIT_NODE = NodeConstants.INIT_NODE
NODE_ITEM_NODE = NodeConstants.ITEM_NODE
NODE_ITEM_RESOLVE_NODE = NodeConstants.ITEM_RESOLVE_NODE
NODE_EVENT_NODE = NodeConstants.EVENT_NODE
NODE_DICE_NODE = NodeConstants.DICE_NODE
NODE_RESOLVE_NODE = NodeConstants.RESOLVE_NODE
NODE_SUMMARY_NODE = NodeConstants.SUMMARY_NODE
NODE_SUGGESTION_NODE = NodeConstants.SUGGESTION_NODE

# Node annotations (used by tooling/visualization)
NODE_CALLABLES_BY_ID = {
    NODE_ROUTER_NODE: router_node,
    NODE_INIT_NODE: init_node,
    # Map both ID versions if necessary, but graph uses NODE_ITEM_RESOLVE_NODE now probably
    NODE_ITEM_RESOLVE_NODE: item_resolve_node,
    NODE_EVENT_NODE: event_node,
    NODE_DICE_NODE: dice_node,
    NODE_RESOLVE_NODE: resolve_node,
    NODE_SUMMARY_NODE: summary_node,
    NODE_SUGGESTION_NODE: suggestion_node,
}

NODE_ANNOTATIONS_BY_ID: dict[str, NodeAnnotation] = {
    node_id: (get_node_annotation(fn) or NodeAnnotation(kind="normal"))
    for node_id, fn in NODE_CALLABLES_BY_ID.items()
}

LLM_NODE_IDS = {k for k, v in NODE_ANNOTATIONS_BY_ID.items() if v.kind == "llm"}
NORMAL_NODE_IDS = {k for k, v in NODE_ANNOTATIONS_BY_ID.items() if v.kind == "normal"}

__all__ = [
    "init_node",
    "item_resolve_node",
    "event_node",
    "dice_node",
    "route_check_dice",
    "resolve_node",
    "router_node",
    "summary_node",
    "suggestion_node",
    "route_event",
    "NODE_ROUTER_NODE",
    "NODE_INIT_NODE",
    "NODE_ITEM_RESOLVE_NODE",
    "NODE_EVENT_NODE",
    "NODE_DICE_NODE",
    "NODE_RESOLVE_NODE",
    "NODE_SUMMARY_NODE",
    "NODE_SUGGESTION_NODE",
    "NodeAnnotation",
    "NodeKind",
    "NODE_CALLABLES_BY_ID",
    "NODE_ANNOTATIONS_BY_ID",
    "LLM_NODE_IDS",
    "NORMAL_NODE_IDS",
]
