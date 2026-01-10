import json
import os

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from backroom_agent.state import State
from backroom_agent.utils.cache import memory_cache
from backroom_agent.utils.common import (extract_json_from_text, get_llm,
                                         load_prompt)
from backroom_agent.utils.logger import logger
from backroom_agent.utils.node_annotation import annotate_node


def _load_init_prompt() -> str:
    """Load the init summary prompt."""
    try:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prompt_path = os.path.join(base_dir, "prompts", "init.prompt")
        return load_prompt(prompt_path)
    except Exception as e:
        logger.error(f"Failed to load init prompt: {e}")
        return "Describe the level {level} based on: {level_context}. Return JSON."


def _generate_llm_intro(level: str, level_context: str) -> dict:
    """Generates the intro JSON using LLM. Used as cache miss callback."""
    logger.info(f"Cache Miss for Init Node: {level}. Generating with LLM.")
    prompt_template = _load_init_prompt()
    
    # Truncate context to avoid token limits
    prompt = prompt_template.format(level=level, level_context=level_context[:15000])
    
    llm = get_llm()
    response = llm.invoke([SystemMessage(content=prompt)])
    content = str(response.content)

    try:
        parsed = extract_json_from_text(content)
        if isinstance(parsed, dict) and "message" in parsed:
            return parsed
    except json.JSONDecodeError:
        logger.warning("Init Node LLM output invalid JSON. Fallback.")

    # Fallback
    return {
        "message": f"You have entered {level}. {content[:100]}...",
        "suggestions": ["Look around"]
    }


@annotate_node("llm")
def init_node(state: State, config: RunnableConfig) -> dict:
    """Handles the initialization event (New Level Entry)."""
    current_game_state = state.get("current_game_state")
    level = current_game_state.level if current_game_state else "Unknown Level"

    logger.info(f"▶ NODE: Init Node (Level: {level})")

    # Use HTML from State (Pre-fetched by Router)
    level_context = state.get("level_context", "")

    # Cache Key: Level ID + Content Hash (simple first 1000 chars)
    # Note: We cache the *dict result* now, not just string
    cache_key_content = f"{level}:{level_context[:1000]}"
    
    result_data = memory_cache.get(
        "init_node_json_v1",
        cache_key_content,
        on_miss=lambda: _generate_llm_intro(level, level_context),
    )

    welcome_msg = result_data.get("message", f"Welcome to {level}.")
    suggestions = result_data.get("suggestions", [])

    logger.info(f"Init Narrative: {welcome_msg[:50]}...")

    return {
        "messages": [AIMessage(content=welcome_msg)],
        "suggestions": suggestions
    }
