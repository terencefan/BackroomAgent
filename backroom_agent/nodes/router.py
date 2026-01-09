import logging
from typing import Dict, Literal

from langgraph.graph import END

from backroom_agent.constants import NodeConstants
from backroom_agent.protocol import EventType
from backroom_agent.state import State
from backroom_agent.utils.level import find_level_data

logger = logging.getLogger(__name__)


def router_node(state: State) -> Dict[Literal["level_context"], str]:
    """
    Router Node:
    1. Pre-fetch level context (HTML) and inject into State.
    2. Does NOT determine the next step directly (Routing logic is separate).
    """
    current_game_state = state.get("current_game_state")
    level_id = current_game_state.level if current_game_state else "Level 0"

    # Check if context is already loaded to avoid redundant reads
    if not state.get("level_context"):
        logger.info(f"Router pre-fetching context for {level_id}")
        _, level_context = find_level_data(level_id)
        if level_context:
            return {"level_context": level_context}

    return {}


def route_event(state: State) -> str:
    """
    Conditional Edge Logic:
    Determines which node to execute based on event type.
    """
    event = state.get("event")
    event_type = event.type if event else EventType.MESSAGE

    if event_type == EventType.INIT:
        return NodeConstants.INIT
    elif event_type == EventType.MESSAGE:
        return NodeConstants.GENERATE
    elif event_type in [EventType.USE, EventType.DROP]:
        return NodeConstants.INVENTORY
    else:
        # Check explicit mappings or fallthrough to END
        return END
