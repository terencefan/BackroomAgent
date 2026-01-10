import json
from typing import Any, Dict

from langchain_core.runnables import RunnableConfig

from backroom_agent.constants import GraphKeys, NodeConstants
from backroom_agent.nodes.resolve_utils import apply_state_updates
from backroom_agent.state import State
from backroom_agent.utils.logger import logger
from backroom_agent.utils.node_annotation import annotate_node


@annotate_node("normal")
def event_resolve_node(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """
    Event Resolve Node:
    Deterministic state updates based on the Dice outcome.
    NO LLM CALLS.
    """
    logger.info("▶ NODE: Event Resolve Node")

    current_state = state.get(GraphKeys.CURRENT_GAME_STATE)
    logic_outcome = state.get(GraphKeys.LOGIC_OUTCOME)

    if not current_state:
        return {}

    # Extract updates from the chosen outcome
    updates = {}
    if logic_outcome:
        # logic_outcome comes from Dice Node, representing the selected EventOutcome
        result = None
        if isinstance(logic_outcome, dict):
            result = logic_outcome.get("result")
        elif hasattr(logic_outcome, "result"):
            result = logic_outcome.result

        if result and isinstance(result, dict):
            # Check for explicit "updates" key (new format)
            if "updates" in result:
                updates = result["updates"]
            # Fallback (legacy/simple): check for direct keys if we flatten structure later
            # But currently we enforce "updates" block.

    if not updates:
        logger.info("No specific state updates found in logic outcome.")
        return {}

    # Apply updates mechanistically
    new_game_state = apply_state_updates(current_state, updates)

    return {
        GraphKeys.CURRENT_GAME_STATE: new_game_state,
    }


def route_settle(state: State) -> str:
    """Decides where to go after Event Resolve."""
    return NodeConstants.SETTLEMENT_NODE
