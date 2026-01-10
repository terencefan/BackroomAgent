import json
import os
from typing import Optional, Tuple, cast

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from backroom_agent.protocol import GameState, LogicEvent
from backroom_agent.state import State
from backroom_agent.utils.common import (extract_json_from_text, get_llm,
                                         load_prompt)
from backroom_agent.utils.logger import logger
from backroom_agent.utils.node_annotation import annotate_node

# Singleton model instance
model = get_llm()


def _load_system_prompt() -> str:
    """Load the system prompt from the prompts directory."""
    try:
        # Construct path relative to the current file (in nodes package)
        # ../prompts/dm_agent.prompt
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prompt_path = os.path.join(base_dir, "prompts", "dm_agent.prompt")
        return load_prompt(prompt_path)
    except FileNotFoundError:
        return "You are a helpful AI Dungeon Master for a Backrooms game."


SYSTEM_PROMPT = _load_system_prompt()


def parse_dm_response(
    content: str,
) -> Tuple[str, Optional[GameState], Optional[LogicEvent]]:
    """
    Parses the JSON response from the DM Agent.

    Args:
        content (str): The raw string content from the LLM response.

    Returns:
        Tuple[str, Optional[GameState], Optional[LogicEvent]]: A tuple containing the narrative text,
        the updated GameState object (or None), and the LogicEvent object (or None).
    """
    narrative_text = content
    new_game_state = None
    logic_event = None

    try:
        # Attempt to parse json
        parsed_output = extract_json_from_text(content)

        # Check standard fields
        if isinstance(parsed_output, dict):
            narrative_text = parsed_output.get("message", content)
            updated_state_dict = parsed_output.get("updated_state")
            event_dict = parsed_output.get("event")

            if updated_state_dict:
                # Reconstruct GameState object
                try:
                    new_game_state = GameState(**updated_state_dict)
                except Exception as e:
                    logger.error(f"Failed to parse updated_state into GameState: {e}")

            if event_dict:
                try:
                    logic_event = LogicEvent(**event_dict)
                except Exception as e:
                    logger.error(f"Failed to parse event into LogicEvent: {e}")

    except json.JSONDecodeError:
        logger.warning(
            "LLM response was not valid JSON. Using raw content as narrative."
        )

    return narrative_text, new_game_state, logic_event


@annotate_node("llm")
def message_node(state: State, config: RunnableConfig) -> dict:
    """
    Handles 'message' events: General dialogue between player and DM.
    """
    logger.info("▶ NODE: Message Node (LLM Generation)")

    messages = state["messages"]
    current_state = state.get("current_game_state")

    # If the last message is from Dice Node (HumanMessage with specific marker?), treat it as system feedback
    # But for now, we just dump all messages.

    debug_content = [
        f"{i}. [{msg.type}]: {msg.content}" for i, msg in enumerate(messages)
    ]
    logger.debug(
        f"State Messages Dump ({len(messages)} items):\n" + "\n".join(debug_content)
    )

    # 1. Prepare Game State Data
    state_dict = {}
    if current_state:
        # Robust Dump (Pydantic v2 preferred)
        try:
            state_dict = current_state.model_dump()
        except AttributeError:
            state_dict = current_state.dict()

    # 2. Extract Current User Message
    current_message = ""
    if messages:
        # Cast content to string (assuming text-only for now)
        msg_content = messages[-1].content
        if isinstance(msg_content, str):
            current_message = msg_content
        else:
            current_message = str(msg_content)

    # 3. Inject Message into State Dict
    state_dict["message"] = current_message

    # 4. Dump to JSON
    json_input = json.dumps(state_dict, ensure_ascii=False, indent=2)

    # Log the JSON Payload
    logger.debug(f"LLM Input Payload (JSON):\n{json.dumps(state_dict, indent=2)}")

    # 5. Invoke LLM
    final_messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=json_input),
    ]

    response = model.invoke(final_messages, config=config)

    # Log the Output Payload
    raw_response_content = response.content
    if not isinstance(raw_response_content, str):
        raw_response_content = str(raw_response_content)

    try:
        parsed_json = json.loads(raw_response_content)
        logger.debug(f"LLM Output Payload (JSON):\n{json.dumps(parsed_json, indent=2)}")
    except json.JSONDecodeError:
        logger.debug(f"LLM Output Payload (Raw/Invalid JSON):\n{raw_response_content}")

    return {"raw_llm_output": raw_response_content}


@annotate_node("normal")
def process_message_node(state: State, config: RunnableConfig) -> dict:
    """
    Processes the raw LLM output from message_node.
    OR processes the Dice Roll feedback loop.
    """
    logger.info("▶ NODE: Process Message Node")

    # Check if we are re-entering from Dice Node
    # The Router (main loop) calls nodes. If we are in process_message_node,
    # it means we were called EITHER by message_node OR by dice_node (per new graph edge).

    # ISSUE: process_message_node currently expects "raw_llm_output".
    # BUT if we come from Dice, we didn't run LLM yet.
    # WE NEED TO RUN LLM HERE if coming from Dice.

    # Actually, the graph edge says: DICE -> PROCESS_MESSAGE.
    # But message_node is where LLM runs.
    # process_message_node just PARSES.

    # If the user wants "Dice -> Generate", they probably mean "Dice -> LLM -> Parse".
    # In my graph, I have NODE_MESSAGE (LLM) and NODE_PROCESS_MESSAGE (Parse).
    # So I should route DICE -> NODE_MESSAGE.

    raw_content = state.get("raw_llm_output", "")
    if raw_content is None:
        raw_content = ""

    current_state = state.get("current_game_state")

    # Parse Output JSON
    narrative_text, new_game_state, logic_event = parse_dm_response(raw_content)

    logger.info(f"LLM Response Narrative: {narrative_text[:50]}...")

    # If LLM didn't return a state (or we removed it from prompt), keep the old one
    if new_game_state is None:
        new_game_state = current_state
    else:
        logger.info("Game State updated by LLM.")

    if logic_event:
        logger.info(f"Logic Event Generated: {logic_event.name}")

    # Create proper AIMessage with just the narrative text
    final_response_message = AIMessage(content=narrative_text)

    return {
        "messages": [final_response_message],
        "current_game_state": new_game_state,
        "logic_event": logic_event,
    }
