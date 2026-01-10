import json
import os
from typing import Any, Dict, List, Optional, Tuple

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


def format_delta(val: int) -> str:
    """Helper to colorize numerical changes (yellow)."""
    sign = "+" if val > 0 else ""
    return f'<span style="color:#ffee00">{sign}{val}</span>'


def format_item_line(prefix: str, name: str) -> str:
    """Helper to colorize item changes."""
    return f'{prefix} <span style="color:#ffee00">{name}</span>'


def apply_state_updates(
    current_state: Any, updates: Dict[str, Any]
) -> Tuple[Any, Optional[str]]:
    """
    Applies updates to state and returns (new_state, log_content).
    log_content is None if no significant changes happened.
    """
    if not current_state:
        return current_state, None

    new_game_state = current_state.model_copy(deep=True)
    if not updates:
        return new_game_state, None

    log_lines = []

    # Support both old "hp_change" and new "hp" keys
    hp_change = int(updates.get("hp", updates.get("hp_change", 0)))
    sanity_change = int(updates.get("sanity", updates.get("sanity_change", 0)))

    new_game_state.vitals.hp = max(
        0, min(new_game_state.vitals.maxHp, new_game_state.vitals.hp + hp_change)
    )
    new_game_state.vitals.sanity = max(
        0, min(100, new_game_state.vitals.sanity + sanity_change)
    )

    if hp_change != 0:
        log_lines.append(f"HP {format_delta(hp_change)}")
    if sanity_change != 0:
        log_lines.append(f"Sanity {format_delta(sanity_change)}")

    if hp_change != 0 or sanity_change != 0:
        logger.info(
            f"Settle/Resolve Applied Updates: HP{hp_change:+} Sanity{sanity_change:+}"
        )

    # Handle Level Transition
    new_level = updates.get("new_level")
    if new_level and isinstance(new_level, str):
        old_level = new_game_state.level
        new_game_state.level = new_level
        log_lines.append(f"Level Transfer: {old_level} -> {format_item_line('', new_level)}")
        logger.info(f"Level Transition detected: {old_level} -> {new_level}")

    # Handle Inventory Updates
    from backroom_agent.protocol import Item

    # 1. Add Items
    items_to_add = updates.get("add_items", [])
    if items_to_add:
        for item_data in items_to_add:
            try:
                # Basic validation
                if "id" not in item_data:
                    # Generate ID from name if missing
                    item_data["id"] = (
                        item_data.get("name", "unknown").lower().replace(" ", "_")
                    )

                new_item = Item(**item_data)

                # Check if item already exists (stack it)
                existing_item = next(
                    (i for i in new_game_state.inventory if i and i.id == new_item.id),
                    None,
                )
                if existing_item:
                    existing_item.quantity += new_item.quantity
                    log_lines.append(format_item_line("+", f"{new_item.name} x{new_item.quantity}"))
                    logger.info(f"Stacked item {new_item.id} (+{new_item.quantity})")
                else:
                    new_game_state.inventory.append(new_item)
                    log_lines.append(format_item_line("+", f"{new_item.name}"))
                    logger.info(f"Added new item {new_item.id}")
            except Exception as e:
                logger.error(f"Failed to add item {item_data}: {e}")

    # 2. Remove Items
    items_to_remove = updates.get("remove_items", [])
    if items_to_remove:
        # Assuming list of IDs
        for item_id_or_name in items_to_remove:
            target_id = str(item_id_or_name).lower()

            # Find item
            # We iterate a copy or index to modify list safely
            # Assuming simple removal of 1 quantity or full removal?
            # Start with full removal/decrement logic

            found_index = -1
            found_name = target_id
            for idx, item in enumerate(new_game_state.inventory):
                if item and (item.id == target_id or item.name.lower() == target_id):
                    found_index = idx
                    found_name = item.name
                    break

            if found_index != -1:
                # For now, just remove 1 quantity.
                item = new_game_state.inventory[found_index]
                if item and item.quantity > 1:
                    item.quantity -= 1
                    logger.info(f"Decremented item {item.id}")
                else:
                    new_game_state.inventory.pop(found_index)
                    logger.info(f"Removed item {target_id}")
                
                log_lines.append(format_item_line("-", found_name))

    # Construct final log string
    log_content = None
    if log_lines:
        log_content = "  \n".join(log_lines) # Two spaces for markdown newline

    return new_game_state, log_content
