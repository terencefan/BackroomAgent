from .init import init_node
from .item import item_node
from .llm import llm_node
from .message import message_node, process_message_node
from .router import route_event, router_node
from .suggestion import suggestion_node
from .summary import summary_node

# Define Node Constants via Reflection
NODE_ROUTER = router_node.__name__
NODE_INIT = init_node.__name__
NODE_ITEM = item_node.__name__
NODE_LLM = llm_node.__name__
NODE_MESSAGE = message_node.__name__
NODE_PROCESS_MESSAGE = process_message_node.__name__
NODE_SUMMARY = summary_node.__name__
NODE_SUGGESTION = suggestion_node.__name__

__all__ = [
    "init_node",
    "item_node",
    "llm_node",
    "message_node",
    "process_message_node",
    "router_node",
    "summary_node",
    "suggestion_node",
    "route_event",
    "NODE_ROUTER",
    "NODE_INIT",
    "NODE_ITEM",
    "NODE_LLM",
    "NODE_MESSAGE",
    "NODE_SUMMARY",
    "NODE_SUGGESTION",
]
