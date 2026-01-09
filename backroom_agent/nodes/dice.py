import logging
from typing import Any, Dict, cast

from langchain_core.messages import HumanMessage

from backroom_agent.constants import GraphKeys, NodeConstants
from backroom_agent.protocol import DiceRoll, LogicEvent
from backroom_agent.state import State
from backroom_agent.utils.dice import Dice

logger = logging.getLogger(__name__)


def route_check_dice(state: State) -> str:
    """
    Conditional Routing:
    Check if a logic_event was generated.
    If yes -> Go to Dice Node.
    If no -> Skip to Summary Node.
    """
    if state.get("logic_event"):
        return NodeConstants.DICE
    return NodeConstants.SUMMARY


def dice_node(state: State) -> Dict[str, Any]:
    """
    Dice Node:
    1. Checks if a logic_event exists in the state.
    2. If so, determines the die type (d20 or d100).
    3. Rolls the die.
    4. Matches the roll result to an outcome in the event.
    5. Updates the game state based on the outcome result.
    6. Returns the dice roll info AND creates a new HumanMessage to feed back to LLM.
    """
    logic_event = state.get("logic_event")

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
    if logic_event.outcomes:
        for outcome in logic_event.outcomes:
            # outcome.range is [min, max]
            if len(outcome.range) == 2:
                min_val, max_val = outcome.range
                if min_val <= roll_result <= max_val:
                    matched_outcome = outcome
                    break

    # Construct feedback message for LLM
    feedback_text = f"Dice Roll Result: [{die_type.upper()}] {roll_result}. Reason: {logic_event.name}."
    if matched_outcome and matched_outcome.result:
        # Add the outcome content (e.g., "Success! You found a key.") so LLM knows what happened
        content = matched_outcome.result.get("content", "")
        feedback_text += f" Outcome: {content}"

        # NOTE: logic_outcome is NOT sent to frontend directly via updates here
        # (unless we want to debug). The LLM will incorporate it into the next narrative.

    logger.info(f"Dice Node Feedback: {feedback_text}")

    # Create a HumanMessage (or SystemMessage) representing the resolved event to continue the flow
    # Using HumanMessage to simulate "System Feedback" in the chat history for the context model
    feedback_msg = HumanMessage(content=feedback_text)

    updates: Dict[str, Any] = {
        GraphKeys.DICE_ROLL: dice_roll,  # For Frontend Animation
        GraphKeys.MESSAGES: [feedback_msg],  # For LLM Context
        GraphKeys.LOGIC_EVENT: None,  # Clear event to prevent loops
    }

    if matched_outcome:
        updates["logic_outcome"] = matched_outcome

    return updates
