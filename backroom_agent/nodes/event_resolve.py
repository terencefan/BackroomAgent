import json
from typing import Any, Dict

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from backroom_agent.constants import GraphKeys, NodeConstants
from backroom_agent.nodes.resolve_utils import (apply_state_updates,
                                                load_settle_prompt,
                                                parse_settle_response,
                                                serialize_game_state,
                                                serialize_messages)
from backroom_agent.state import State
from backroom_agent.utils.common import get_llm
from backroom_agent.utils.logger import logger
from backroom_agent.utils.node_annotation import annotate_node

SETTLE_PROMPT = load_settle_prompt()


@annotate_node("llm")
def event_resolve_node(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """
    Event Resolve Node (formerly Settle Node):
    Resolves the turn for non-dice paths (or cleanup), deciding implicit state changes based on narrative.
    """
    logger.info("▶ NODE: Event Resolve Node")

    # 1. Prepare Input
    messages = state.get(GraphKeys.MESSAGES, [])
    serialized_msgs = serialize_messages(messages)

    current_state = state.get(GraphKeys.CURRENT_GAME_STATE)
    gs_data = serialize_game_state(current_state)

    logic_outcome = state.get(GraphKeys.LOGIC_OUTCOME)
    if hasattr(logic_outcome, "model_dump"):
        logic_outcome = logic_outcome.model_dump()  # type: ignore
    elif hasattr(logic_outcome, "dict"):
        logic_outcome = logic_outcome.dict()  # type: ignore

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
    new_game_state = apply_state_updates(current_state, updates)

    return {
        GraphKeys.CURRENT_GAME_STATE: new_game_state,
    }


def route_settle(state: State) -> str:
    """Decides where to go after Event Resolve."""
    return NodeConstants.SETTLEMENT_NODE
