import json
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from backroom_agent.constants import GraphKeys
from backroom_agent.nodes.resolve_utils import (apply_state_updates,
                                                load_settle_prompt,
                                                parse_settle_response,
                                                serialize_game_state,
                                                serialize_messages)
from backroom_agent.protocol import EventType
from backroom_agent.state import State
from backroom_agent.utils.common import get_llm
from backroom_agent.utils.logger import logger
from backroom_agent.utils.node_annotation import annotate_node

SETTLE_PROMPT = load_settle_prompt()


@annotate_node("llm")
def item_resolve_node(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """
    Item Resolve Node (Inventory Resolve):
    Handles item usage/drop events using the Settle Prompt logic to update state.
    """
    logger.info("▶ NODE: Item Resolve Node")

    # 1. Prepare Input
    messages = state.get(GraphKeys.MESSAGES, [])
    serialized_msgs = serialize_messages(messages)

    current_state = state.get(GraphKeys.CURRENT_GAME_STATE)
    gs_data = serialize_game_state(current_state)

    event = state.get("event")
    # logic_outcome logic for items
    if event:
        logic_outcome = {
            "type": "item_interaction",
            "item_id": event.item_id,
            "action": event.type,  # 'use' or 'drop'
            "quantity": event.quantity,
        }
    else:
        logic_outcome = {"error": "No event found"}

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
    data = parse_settle_response(content)

    updates = data.get("state_updates", {})
    new_game_state, log_content = apply_state_updates(current_state, updates)

    messages_out = []
    if log_content:
        messages_out.append(SystemMessage(content=log_content))

    # Note: We do NOT append an AIMessage here. The Summary Node should describe the effect.
    return {
        GraphKeys.CURRENT_GAME_STATE: new_game_state,
        GraphKeys.LOGIC_OUTCOME: logic_outcome,
        GraphKeys.MESSAGES: messages_out,
    }
