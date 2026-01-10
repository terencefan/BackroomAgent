import json
import os
from typing import Any, Dict, List, Optional

from langchain_core.messages import AIMessage, SystemMessage

from backroom_agent.utils.common import load_prompt
from backroom_agent.utils.logger import logger


def load_settle_prompt() -> str:
    """Load the settle prompt from the prompts directory."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        # renamed from settle.prompt to resolve.prompt
        prompt_path = os.path.join(base_dir, "prompts", "resolve.prompt")
        return load_prompt(prompt_path)
    except FileNotFoundError:
        return "You are the resolver. Output JSON with 'narrative' and 'next_step'."


def serialize_messages(messages: List[Any]) -> List[Dict[str, str]]:
    serialized_msgs = []
    for msg in messages:
        if isinstance(msg, AIMessage):
            role = "ai"
        elif isinstance(msg, SystemMessage):
            role = "system"
        else:
            role = "human"
        serialized_msgs.append({"role": role, "content": str(msg.content)})
    return serialized_msgs


def serialize_game_state(current_state: Optional[Any]) -> Dict[str, Any]:
    if not current_state:
        return {}
    if hasattr(current_state, "model_dump"):
        return current_state.model_dump()
    elif hasattr(current_state, "dict"):
        return current_state.dict()
    return current_state  # type: ignore


def parse_settle_response(content: str) -> Dict[str, Any]:
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
        return json.loads(content)
    except Exception:
        return {}


def apply_state_updates(current_state: Any, updates: Dict[str, Any]) -> Any:
    if not current_state:
        return current_state

    new_game_state = current_state.model_copy(deep=True)
    if not updates:
        return new_game_state

    hp_change = int(updates.get("hp_change", 0))
    sanity_change = int(updates.get("sanity_change", 0))

    new_game_state.vitals.hp = max(
        0, min(new_game_state.vitals.maxHp, new_game_state.vitals.hp + hp_change)
    )
    new_game_state.vitals.sanity = max(
        0, min(100, new_game_state.vitals.sanity + sanity_change)
    )

    if hp_change != 0 or sanity_change != 0:
        logger.info(
            f"Settle/Resolve Applied Updates: HP{hp_change:+} Sanity{sanity_change:+}"
        )

    # Handle Level Transition
    new_level = updates.get("new_level")
    if new_level and isinstance(new_level, str):
        old_level = new_game_state.level
        new_game_state.level = new_level
        logger.info(f"Level Transition detected: {old_level} -> {new_level}")

    # Note: Inventory updates (items_added/removed) logic placeholder
    # Future implementation goes here.

    return new_game_state
