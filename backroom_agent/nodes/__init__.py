from backroom_agent.constants import NodeConstants

from .dice import dice_node, route_check_dice
from .init import init_node
from .item import item_node
from .message import message_node, process_message_node
from .router import route_event, router_node
from .suggestion import suggestion_node
from .summary import summary_node

# Define Node Constants (Aliases to centralized constants)
NODE_ROUTER = NodeConstants.ROUTER
NODE_INIT = NodeConstants.INIT
NODE_INVENTORY = NodeConstants.INVENTORY
NODE_GENERATE = NodeConstants.GENERATE
NODE_PROCESS = NodeConstants.PROCESS
NODE_DICE = NodeConstants.DICE
NODE_SUMMARY = NodeConstants.SUMMARY
NODE_SUGGEST = NodeConstants.SUGGEST

__all__ = [
    "init_node",
    "item_node",
    "message_node",
    "process_message_node",
    "dice_node",
    "route_check_dice",
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
    "NODE_SUMMARY",
    "NODE_SUGGEST",
]
