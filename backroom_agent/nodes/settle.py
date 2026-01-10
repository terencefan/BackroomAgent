import json
import os
from typing import Any, Dict, List, Literal, Optional

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from backroom_agent.constants import GraphKeys, NodeConstants
from backroom_agent.state import State
from backroom_agent.utils.common import get_llm, load_prompt
from backroom_agent.utils.logger import logger
from backroom_agent.utils.node_annotation import annotate_node


def _load_settle_prompt() -> str:
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prompt_path = os.path.join(base_dir, "prompts", "settle.prompt")
        return load_prompt(prompt_path)
    except FileNotFoundError:
        return "You are the resolver. Output JSON with 'narrative' and 'next_step'."


SETTLE_PROMPT = _load_settle_prompt()


def _serialize_messages(messages: List[Any]) -> List[Dict[str, str]]:
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


def _serialize_game_state(current_state: Optional[Any]) -> Dict[str, Any]:
    if not current_state:
        return {}
    if hasattr(current_state, "model_dump"):
        return current_state.model_dump()
    elif hasattr(current_state, "dict"):
        return current_state.dict()
    return current_state  # type: ignore


def _parse_llm_response(content: str) -> Dict[str, Any]:
    try:
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()
        return json.loads(content)
    except Exception:
        return {}


def _apply_state_updates(current_state: Any, updates: Dict[str, Any]) -> Any:
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
            f"Settle Node Applied Updates: HP{hp_change:+} Sanity{sanity_change:+}"
        )

    # Note: Inventory updates (items_added/removed) logic is currently
    # a placeholder as it requires complex item lookup/matching.
    # Future implementation goes here.

    return new_game_state


@annotate_node("llm")
def settle_node(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """
    Settle Node: Resolves the turn, blending dice results if any, and deciding next step.
    """
    logger.info("▶ NODE: Settle Node")

    # 1. Prepare Input
    messages = state.get(GraphKeys.MESSAGES, [])
    serialized_msgs = _serialize_messages(messages)
    
    current_state = state.get(GraphKeys.CURRENT_GAME_STATE)
    gs_data = _serialize_game_state(current_state)

    logic_outcome = state.get(GraphKeys.LOGIC_OUTCOME)
    if hasattr(logic_outcome, "model_dump"):
        logic_outcome = logic_outcome.model_dump()
    elif hasattr(logic_outcome, "dict"):
        logic_outcome = logic_outcome.dict()
    
    input_data = {
        "current_game_state": gs_data,
        "interaction_messages": serialized_msgs,
        "logic_outcome": logic_outcome,
    }
    user_content = json.dumps(input_data, ensure_ascii=False, indent=2)

    # 2. Invoke LLM
    llm = get_llm()
    response = llm.invoke(
        [SystemMessage(content=SETTLE_PROMPT), HumanMessage(content=user_content)]
    )
    content = str(response.content)

    # 3. Process Response
    data = _parse_llm_response(content)
    
    updates = data.get("state_updates", {})
    new_game_state = _apply_state_updates(current_state, updates)

    return {
        GraphKeys.CURRENT_GAME_STATE: new_game_state,
    }


def route_settle(state: State) -> str:
        """Decides where to go after Settle.

        Note:
        - Routing functions should be pure (no state mutation). Mutating `state` here does not
            reliably persist across LangGraph steps.
        - The dice follow-up narrative loop is handled in the graph edges (Dice -> Generate).
        """

        # Settle is the last resolver step; always proceed to summary.
        logger.debug("Route Settle -> SUMMARY")
        return NodeConstants.SUMMARY
