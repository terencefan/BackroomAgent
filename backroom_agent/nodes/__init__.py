from backroom_agent.constants import NodeConstants
from backroom_agent.utils.node_annotation import (NodeAnnotation, NodeKind,
                                                  get_node_annotation)

from .dice import dice_node, route_check_dice
from .init import init_node
from .item import item_node
from .message import message_node
from .router import route_event, router_node
from .settle import route_settle, settle_node
from .suggestion import suggestion_node
from .summary import summary_node

# Define Node Constants (Aliases to centralized constants)
NODE_ROUTER_NODE = NodeConstants.ROUTER_NODE
NODE_INIT_NODE = NodeConstants.INIT_NODE
NODE_ITEM_NODE = NodeConstants.ITEM_NODE
NODE_MESSAGE_NODE = NodeConstants.MESSAGE_NODE
NODE_DICE_NODE = NodeConstants.DICE_NODE
NODE_SETTLE_NODE = NodeConstants.SETTLE_NODE
NODE_SUMMARY_NODE = NodeConstants.SUMMARY_NODE
NODE_SUGGESTION_NODE = NodeConstants.SUGGESTION_NODE

# Node annotations (used by tooling/visualization)
NODE_CALLABLES_BY_ID = {
    NODE_ROUTER_NODE: router_node,
    NODE_INIT_NODE: init_node,
    NODE_ITEM_NODE: item_node,
    NODE_MESSAGE_NODE: message_node,
    NODE_DICE_NODE: dice_node,
    NODE_SETTLE_NODE: settle_node,
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
    "item_node",
    "message_node",
    "dice_node",
    "route_check_dice",
    "settle_node",
    "route_settle",
    "router_node",
    "summary_node",
    "suggestion_node",
    "route_event",
    "NODE_ROUTER_NODE",
    "NODE_INIT_NODE",
    "NODE_ITEM_NODE",
    "NODE_MESSAGE_NODE",
    "NODE_DICE_NODE",
    "NODE_SETTLE_NODE",
    "NODE_SUMMARY_NODE",
    "NODE_SUGGESTION_NODE",
    "NodeAnnotation",
    "NodeKind",
    "NODE_CALLABLES_BY_ID",
    "NODE_ANNOTATIONS_BY_ID",
    "LLM_NODE_IDS",
    "NORMAL_NODE_IDS",
]
