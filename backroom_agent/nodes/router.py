from typing import Dict, Literal

from langchain_core.messages import HumanMessage
from langgraph.graph import END

from backroom_agent.constants import NodeConstants
from backroom_agent.protocol import EventType
from backroom_agent.state import State
from backroom_agent.utils.level import find_level_data
from backroom_agent.utils.logger import logger
from backroom_agent.utils.node_annotation import annotate_node


@annotate_node("normal")
def router_node(state: State) -> Dict[Literal["level_context"], str]:
    """
    Router Node:
    1. Pre-fetch level context (HTML) and inject into State.
    2. Does NOT determine the next step directly (Routing logic is separate).
    """
    logger.info("▶ NODE: Router Node")

    current_game_state = state.get("current_game_state")
    level_id = current_game_state.level if current_game_state else "Level 0"

    # Check if context is already loaded to avoid redundant reads
    updates = {"turn_loop_count": 0}
    
    if not state.get("level_context"):
        logger.info(f"Router pre-fetching context for {level_id}")
        _, level_context = find_level_data(level_id)
        if level_context:
            updates["level_context"] = level_context

    # If explicit INIT event, inject a prompt for the Event Node so it has "User Input"
    # NOTE: Init Node now handles INIT events directly, so no synthetic message needed for it.
    event = state.get("event")
    if event:
        if event.type == EventType.USE:
            item_name = event.item_id or "Unknown Item"
            logger.info(f"Router: Injecting trigger message for Use Item: {item_name}")
            updates["messages"] = [HumanMessage(content=f"我使用了物品: {item_name}")]
        elif event.type == EventType.DROP:
            item_name = event.item_id or "Unknown Item"
            qty = event.quantity or 1
            logger.info(f"Router: Injecting trigger message for Drop Item: {item_name}")
            updates["messages"] = [HumanMessage(content=f"我丢弃了物品: {item_name} (数量: {qty})")]

    return updates


def route_event(state: State) -> str:
    """
    Conditional Edge Logic:
    Determines which node to execute based on event type.
    """
    event = state.get("event")
    event_type = event.type if event else EventType.MESSAGE

    if event_type == EventType.INIT:
        return NodeConstants.INIT_NODE
    elif event_type == EventType.MESSAGE:
        return NodeConstants.EVENT_NODE
    elif event_type in [EventType.USE, EventType.DROP]:
        return NodeConstants.EVENT_NODE
    else:
        # Check explicit mappings or fallthrough to END
        return END
