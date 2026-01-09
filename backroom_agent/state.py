from typing import Annotated, List, Optional, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

from backroom_agent.protocol import GameEvent, GameState, LogicEvent, DiceRoll


class State(TypedDict):
    """The shared state of the Backroom Agent graph."""

    messages: Annotated[List[BaseMessage], add_messages]

    # Event Context
    event: GameEvent
    user_input: Optional[str]
    session_id: Optional[str]

    # Snapshot of game state passed from backend
    current_game_state: Optional[GameState]

    # Logic Event (if generated)
    logic_event: Optional[LogicEvent]

    # Dice Roll (if generated)
    dice_roll: Optional[DiceRoll]

    # Raw LLM Output (Intermediate)
    raw_llm_output: Optional[str]

    # Context Data
    level_context: Optional[str]
    valid_actions: Optional[List[str]]

    # Output
    suggestions: Optional[List[str]]
