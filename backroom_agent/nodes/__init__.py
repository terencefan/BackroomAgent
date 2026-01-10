from backroom_agent.constants import NodeConstants
from backroom_agent.utils.node_annotation import (NodeAnnotation, NodeKind,
                                                  get_node_annotation)

from .dice import dice_node, route_check_dice
from .init import init_node
from .item import item_node
from .message import message_node, process_message_node
from .router import route_event, router_node
from .settle import route_settle, settle_node
from .suggestion import suggestion_node
from .summary import summary_node

# Define Node Constants (Aliases to centralized constants)
NODE_ROUTER = NodeConstants.ROUTER
NODE_INIT = NodeConstants.INIT
NODE_INVENTORY = NodeConstants.INVENTORY
NODE_GENERATE = NodeConstants.GENERATE
NODE_PROCESS = NodeConstants.PROCESS
NODE_DICE = NodeConstants.DICE
NODE_SETTLE = NodeConstants.SETTLE
NODE_SUMMARY = NodeConstants.SUMMARY
NODE_SUGGEST = NodeConstants.SUGGEST

# Node annotations (used by tooling/visualization)
NODE_CALLABLES_BY_ID = {
    NODE_ROUTER: router_node,
    NODE_INIT: init_node,
    NODE_INVENTORY: item_node,
    NODE_GENERATE: message_node,
    NODE_PROCESS: process_message_node,
    NODE_DICE: dice_node,
    NODE_SETTLE: settle_node,
    NODE_SUMMARY: summary_node,
    NODE_SUGGEST: suggestion_node,
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
    "process_message_node",
    "dice_node",
    "route_check_dice",
    "settle_node",
    "route_settle",
    "router_node",
    "summary_node",
    "suggestion_node",
    "route_event",
    "NODE_ROUTER",
    "NODE_INIT",
    "NODE_INVENTORY",
    "NODE_GENERATE",
    "NODE_PROCESS",
    "NODE_DICE",
    "NODE_SETTLE",
    "NODE_SUMMARY",
    "NODE_SUGGEST",
    "NodeAnnotation",
    "NodeKind",
    "NODE_CALLABLES_BY_ID",
    "NODE_ANNOTATIONS_BY_ID",
    "LLM_NODE_IDS",
    "NORMAL_NODE_IDS",
]
