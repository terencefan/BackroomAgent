from typing import Any, Dict, cast

from langchain_core.messages import HumanMessage, SystemMessage

from backroom_agent.constants import GraphKeys, NodeConstants
from backroom_agent.nodes.resolve_utils import apply_state_updates
from backroom_agent.protocol import DiceRoll, LogicEvent
from backroom_agent.state import State
from backroom_agent.utils.dice import Dice
from backroom_agent.utils.logger import logger
from backroom_agent.utils.node_annotation import annotate_node


def route_check_dice(state: State) -> str:
    """
    Conditional Routing:
    Check if a logic_event was generated.
    If yes -> Go to Dice Node.
    If no -> Skip to Resolve Node.
    """
    if state.get(GraphKeys.LOGIC_EVENT):
        return NodeConstants.DICE_NODE
    return NodeConstants.RESOLVE_NODE


@annotate_node("normal")
def dice_node(state: State) -> Dict[str, Any]:
    """
    Dice Node:
    1. Checks if a logic_event exists in the state.
    2. Rolls the die and determines outcome.
    3. IMMEDIATELY applies state updates mechanistically.
    4. Returns dice roll, feedback message, and UPDATED STATE.
    """
    logger.info("▶ NODE: Dice Node")

    logic_event = state.get("logic_event")
    current_state = state.get(GraphKeys.CURRENT_GAME_STATE)

    # If no event, return empty (Router should prevent this)
    if not logic_event:
        return {}

    # Cast to LogicEvent for type checker
    logic_event = cast(LogicEvent, logic_event)

    logger.info(
        f"Dice Node: Processing event '{logic_event.name}' with {logic_event.die_type}"
    )

    # Initialize Dice
    dice = Dice()

    # Roll Logic
    die_type = logic_event.die_type
    roll_result = 0

    if die_type == "d20":
        roll_result = dice.d20()
    elif die_type == "d100":
        roll_result = dice.d100()
    elif die_type == "d6":
        roll_result = dice.d6()
    else:
        # Fallback or error handling
        logger.warning(f"Unknown die type: {die_type}, defaulting to d20")
        roll_result = dice.d20()
        die_type = "d20"

    # Construct DiceRoll object
    dice_roll = DiceRoll(
        type=die_type,
        result=roll_result,
        reason=logic_event.name,
    )

    # Outcome Matching
    matched_outcome = None
    outcome_msg = ""
    updates = {}

    if logic_event.outcomes:
        for outcome in logic_event.outcomes:
            # outcome.range is [min, max]
            if len(outcome.range) == 2:
                min_val, max_val = outcome.range
                if min_val <= roll_result <= max_val:
                    matched_outcome = outcome
                    break

    if matched_outcome and matched_outcome.result:
        result = matched_outcome.result
        # Add the outcome content (e.g., "Success! You found a key.") so LLM knows what happened
        content = result.get("content", "")
        feedback_text = f"Dice Roll Result: [{die_type.upper()}] {roll_result}. Reason: {logic_event.name}. Outcome: {content}"

        # Extract updates
        if "updates" in result:
            updates = result["updates"]
        elif "hp_change" in result or "sanity_change" in result:
            updates = result
    else:
        feedback_text = f"Dice Roll Result: [{die_type.upper()}] {roll_result}. Reason: {logic_event.name}."

    logger.info(f"Dice Node Feedback: {feedback_text}")

    # Apply State Updates
    new_game_state, log_content = apply_state_updates(current_state, updates)

    # 1. System Feedback for LLM (HumanMessage)
    feedback_msg = HumanMessage(content=feedback_text)
    
    messages_to_add = [feedback_msg]
    
    # 2. System Status Update (SystemMessage) - Intended for Client UI display
    if log_content:
        system_status_msg = SystemMessage(content=log_content)
        messages_to_add.append(system_status_msg)

    return {
        GraphKeys.DICE_ROLL: dice_roll,  # For Frontend Animation
        GraphKeys.MESSAGES: messages_to_add,  # For LLM Context
        GraphKeys.LOGIC_EVENT: None,  # Clear event to prevent loops
        GraphKeys.CURRENT_GAME_STATE: new_game_state,  # Updated State
        GraphKeys.LOGIC_OUTCOME: matched_outcome,  # Optional: Keep for debugging
    }
