import os

from langchain_core.messages import AIMessage, SystemMessage
from langchain_core.runnables import RunnableConfig

from backroom_agent.state import State
from backroom_agent.utils.cache import memory_cache
from backroom_agent.utils.common import get_llm, load_prompt
from backroom_agent.utils.level import find_level_data
from backroom_agent.utils.logger import logger
from backroom_agent.utils.node_annotation import annotate_node


def _load_init_prompt() -> str:
    """Load the init summary prompt."""
    try:
        # backroom_agent/nodes/init.py -> backroom_agent/
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prompt_path = os.path.join(base_dir, "prompts", "init_summary.prompt")
        return load_prompt(prompt_path)
    except Exception as e:
        logger.error(f"Failed to load init prompt: {e}")
        return (
            "You are the narrator. Describe the level {level} based on: {level_context}"
        )


def _generate_llm_intro(level: str, level_context: str) -> str:
    """Generates the intro using LLM. Used as cache miss callback."""
    logger.info(f"Cache Miss for Init Node: {level}. Generating with LLM.")
    prompt_template = _load_init_prompt()
    # Truncate context to avoid token limits, but enough to be unique and useful
    prompt = prompt_template.format(level=level, level_context=level_context[:15000])
    llm = get_llm()
    return str(llm.invoke([SystemMessage(content=prompt)]).content)


@annotate_node("llm")
def init_node(state: State, config: RunnableConfig) -> dict:
    """Handles the initialization event."""
    current_game_state = state.get("current_game_state")
    level = current_game_state.level if current_game_state else "Unknown Level"

    logger.info(f"▶ NODE: Init Node (Level: {level})")

    # Use HTML from State (Pre-fetched by Router)
    level_context = state.get("level_context")

    # Use LLM to generate description if HTML is available
    if level_context:
        cache_key_content = f"{level}:{level_context[:1000]}"
        welcome_msg = memory_cache.get(
            "init_node_intro",
            cache_key_content,
            on_miss=lambda: _generate_llm_intro(level, level_context),
        )
    else:
        # Fallback if no HTML found
        msg_parts = [f"Welcome to the Backrooms. You are in {level}."]
        msg_parts.append("The hum is defining.")
        welcome_msg = "\n".join(msg_parts)

    return {"messages": [AIMessage(content=welcome_msg)]}
