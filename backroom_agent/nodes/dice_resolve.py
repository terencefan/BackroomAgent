import json
from typing import Any, Dict

from langchain_core.runnables import RunnableConfig

from backroom_agent.constants import GraphKeys
from backroom_agent.nodes.resolve_utils import apply_state_updates
from backroom_agent.state import State
from backroom_agent.utils.logger import logger
from backroom_agent.utils.node_annotation import annotate_node


@annotate_node("normal")
def dice_resolve_node(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """
    Dice Resolve Node:
    Takes the recent Dice Roll outcome and applies state mechanics mechanistically.
    NO LLM CALLS.
    """
    logger.info("▶ NODE: Dice Resolve Node")

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
            elif "hp_change" in result or "sanity_change" in result:
                updates = result

    if not updates:
        logger.info("No specific state updates found in logic outcome (dice path).")
        # For Dice path, we might want to return empty updates effectively
        # The narrative will be handled in the next loop of Event Node
        return {}

    # Apply updates mechanistically
    new_game_state = apply_state_updates(current_state, updates)

    return {
        GraphKeys.CURRENT_GAME_STATE: new_game_state,
    }
