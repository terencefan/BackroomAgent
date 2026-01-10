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


def format_val_custom(val: int, color: str) -> str:
    """Helper to colorize numerical changes with specific color."""
    sign = "+" if val >= 0 else ""
    return f'<span style="color:{color}">{sign}{val}</span>'


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

    vitals_parts = []
    item_changes = []

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
        # Red color for HP #e53e3e
        vitals_parts.append(
            f'<span style="color:#e53e3e; font-weight:bold;">生命值 {format_val_custom(hp_change, "#e53e3e")}</span>'
        )
    if sanity_change != 0:
        # Purple color for Sanity #805ad5
        vitals_parts.append(
            f'<span style="color:#805ad5; font-weight:bold;">理智值 {format_val_custom(sanity_change, "#805ad5")}</span>'
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
        # Add to item_changes for now as a general event line, or separate?
        # User requested item grouping. Level transition is special.
        # Let's put it on its own line if it happens.
        pass

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

                item_label = new_item.name
                if existing_item:
                    existing_item.quantity += new_item.quantity
                    logger.info(f"Stacked item {new_item.id} (+{new_item.quantity})")
                    if new_item.quantity > 1:
                        item_label += f" x{new_item.quantity}"
                else:
                    new_game_state.inventory.append(new_item)
                    logger.info(f"Added new item {new_item.id}")

                # Use yellow for item additions
                item_changes.append(
                    f'<span>+ <span style="color:#ffee00">{item_label}</span></span>'
                )

            except Exception as e:
                logger.error(f"Failed to add item {item_data}: {e}")

    # 2. Remove Items
    items_to_remove = updates.get("remove_items", [])
    if items_to_remove:
        # Assuming list of IDs
        for item_id_or_name in items_to_remove:
            target_id = str(item_id_or_name).lower()

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

                # Use yellow for item removals too, consistent highlighting
                item_changes.append(
                    f'<span>- <span style="color:#ffee00">{found_name}</span></span>'
                )

    # Construct final HTML structure
    # Container
    html_parts = [
        '<div style="display:flex; flex-direction:column; align-items:center; gap:4px; font-size:0.95em;">'
    ]

    # 1. Row: Vitals
    if vitals_parts:
        html_parts.append(
            f'<div style="display:flex; justify-content:center; gap:16px;">{" ".join(vitals_parts)}</div>'
        )

    # 2. Row: Level Transition (if any)
    if new_level and isinstance(new_level, str):
        # old_level was captured above locally? No, need to recapture or just print new
        # Let's just say "Level Transfer: X"
        html_parts.append(
            f'<div style="text-align:center;">Level Transfer: <span style="color:#ffee00">{new_level}</span></div>'
        )

    # 3. Row: Items (Wrapped)
    if item_changes:
        # Flex wrap container for items
        items_html = " ".join(item_changes)
        html_parts.append(
            f'<div style="display:flex; flex-wrap:wrap; justify-content:center; gap:12px;">{items_html}</div>'
        )

    html_parts.append("</div>")

    log_content = None
    if vitals_parts or item_changes or new_level:
        log_content = "".join(html_parts)

    return new_game_state, log_content
