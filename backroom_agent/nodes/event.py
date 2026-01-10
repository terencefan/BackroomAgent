import json
import os
from typing import Optional, Tuple, cast

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from backroom_agent.protocol import GameState, LogicEvent
from backroom_agent.state import State
from backroom_agent.utils.common import (dict_from_pydantic,
                                         extract_json_from_text, get_llm,
                                         load_prompt)
from backroom_agent.utils.level import find_level_data
from backroom_agent.utils.logger import logger
from backroom_agent.utils.node_annotation import annotate_node

# Singleton model instance
model = get_llm()


def _load_system_prompt() -> str:
    """Load the system prompt from the prompts directory."""
    try:
        # Construct path relative to the current file (in nodes package)
        # ../prompts/event.prompt
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prompt_path = os.path.join(base_dir, "prompts", "event.prompt")
        return load_prompt(prompt_path)
    except FileNotFoundError:
        logger.error("System prompt not found. Using default.")
        return "You are a helpful AI Dungeon Master for a Backrooms game."


SYSTEM_PROMPT = _load_system_prompt()


def parse_dm_response(
    content: str,
) -> Tuple[str, Optional[GameState], Optional[LogicEvent], list[str]]:
    """
    Parses the JSON response from the DM Agent.

    Args:
        content (str): The raw string content from the LLM response.

    Returns:
        Tuple[str, Optional[GameState], Optional[LogicEvent], list[str]]: 
        narrative text, updated GameState, LogicEvent, and list of suggestion strings.
    """
    narrative_text = content
    new_game_state = None
    logic_event = None
    suggestions = []

    try:
        # Attempt to parse json
        parsed_output = extract_json_from_text(content)

        # Check standard fields
        if isinstance(parsed_output, dict):
            narrative_text = parsed_output.get("message", content)
            updated_state_dict = parsed_output.get("updated_state")
            event_dict = parsed_output.get("event")
            suggestions = parsed_output.get("suggestions", [])

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
        else:
            logger.warning(
                f"Parsed LLM output is not a dictionary (got {type(parsed_output)}). Treating as narrative."
            )

    except json.JSONDecodeError:
        logger.warning(
            "LLM response was not valid JSON. Using raw content as narrative."
        )

    return narrative_text, new_game_state, logic_event, suggestions


def _prepare_level_context(level_id: str) -> str:
    """Retrieves and dumps level data JSON."""
    level_data_json, _ = find_level_data(level_id)
    if not level_data_json:
        logger.warning(f"Level data for {level_id} not found.")
        level_data_json = {"level_id": level_id, "error": "Level data not found"}
    return json.dumps(level_data_json, ensure_ascii=False, indent=2)


def _prepare_player_input(state_dict: dict, current_message: str) -> str:
    """Constructs the player input JSON string matching local GameState + Input."""
    input_data = {
        "state": state_dict,
        "input": current_message,
    }
    return json.dumps(input_data, ensure_ascii=False, indent=2)

def _prepare_loop_context(loops: int) -> str:
    return json.dumps({"dice_loops": loops}, indent=2)


@annotate_node("llm")
def event_node(state: State, config: RunnableConfig) -> dict:
    """
    Event Node (LLM Driver):
    Orchestrates the main interaction between Player and DM.

    Process:
    1.  **Context Preparation**:
        -   Extracts GameState from LangGraph state.
        -   Fetches static Level Data (Message 1).
        -   Constructs Player Input JSON (Message 2).
        -   Passes loop count to control event generation frequency.
    2.  **LLM Invocation**:
        -   Sends System Prompt + Level Data + Player Input + Loop Context.
        -   LLM acts as DM, generating narrative and potential probability events.
    3.  **Response Parsing**:
        -   Parses JSON response.
        -   Extracts `message` (narrative text).
        -   Extracts `event` (LogicEvent for dice rolls).
        -   Extracts `suggestions` (Guide for next actions).
        -   Updates local GameState if provided.
    4.  **State Update**:
        -   Returns new messages, events, and suggestions to the graph.

    Protocol:
    -   Input: Two consecutive JSON messages.
    -   Output: Strict JSON schema (see `event.prompt`).
    """
    logger.info("▶ NODE: Event Node (LLM Generation)")

    messages = state["messages"]
    current_state = state.get("current_game_state")
    loop_count = state.get("turn_loop_count", 0)

    # 1. Prepare Game State Data
    state_dict = {}
    if current_state:
        state_dict = dict_from_pydantic(current_state)

    # 2. Extract Current User Message
    current_message = ""
    if messages:
        msg_content = messages[-1].content
        current_message = str(msg_content)

    logger.info(f"Player Input: {current_message}")

    # 3. Construct Context Messages
    level_id = state_dict.get("level", "Level 0")

    # Message 1: Static Environment Data
    level_context_str = _prepare_level_context(level_id)

    # Message 2: Dynamic Player State & Input
    player_input_str = _prepare_player_input(state_dict, current_message)

    # Message 3: Loop Context
    loop_context_str = _prepare_loop_context(loop_count)

    # Log Payload (Truncated for readability)
    logger.debug(f"LLM Input (Level Context): {level_context_str[:100]}...")
    logger.debug(f"LLM Input (Player State): {player_input_str[:100]}...")
    logger.debug(f"LLM Input (Loop Context): {loop_context_str}")

    # 4. Invoke LLM
    final_messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=level_context_str),
        HumanMessage(content=player_input_str),
        HumanMessage(content=loop_context_str),
    ]

    response = model.invoke(final_messages, config=config)

    # 5. Process Response
    raw_response_content = str(response.content)

    try:
        # Just logging valid JSON for debugging
        parsed_debug = json.loads(raw_response_content)
        # logger.debug(f"LLM Output Payload (JSON):\n{json.dumps(parsed_debug, indent=2)}")
    except json.JSONDecodeError:
        logger.debug(f"LLM Output Payload (Raw):\n{raw_response_content}")

    narrative_text, new_game_state, logic_event, suggestions = parse_dm_response(
        raw_response_content
    )

    logger.info(f"LLM Narrative: {narrative_text[:50]}...")

    if new_game_state is None:
        new_game_state = current_state

    if logic_event:
        logger.info(f"Generated Logic Event: {logic_event.name}")
        # Clear suggestions if an event is generated to avoid confusing UI,
        # unless we support simultaneous display (which frontend does, but conceptually suggestions are for next turn)
        # But wait, if event is generated, the user MUST roll dice, so they can't take suggestion actions yet.
        suggestions = []
    elif suggestions:
        logger.info(f"Generated Suggestions: {suggestions}")
    else:
        logger.info("Generated Narrative Only (No Event or Suggestions)")

    final_response_message = AIMessage(content=narrative_text)

    return {
        "messages": [final_response_message],
        "current_game_state": new_game_state,
        "logic_event": logic_event,
        "raw_llm_output": raw_response_content,
        "suggestions": suggestions,
    }


# process_message_node removed as it is merged into message_node
