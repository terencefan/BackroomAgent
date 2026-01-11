import os

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig

from backroom_agent.agent.state import State
from backroom_agent.utils.common import get_llm, load_prompt
from backroom_agent.utils.node_annotation import annotate_node

# Singleton model instance
model = get_llm()


def _load_system_prompt() -> str:
    """Load the system prompt from the prompts directory."""
    try:
        # Construct path relative to the current file (in nodes package)
        # ../prompts/dm_agent.prompt
        # Note: __file__ is inside backroom_agent/nodes/
        # base is backroom_agent/
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        prompt_path = os.path.join(base_dir, "prompts", "dm_agent.prompt")
        return load_prompt(prompt_path)
    except FileNotFoundError:
        return "You are a helpful AI Dungeon Master for a Backrooms game."


SYSTEM_PROMPT = _load_system_prompt()


@annotate_node("llm")
def llm_node(state: State, config: RunnableConfig) -> dict:
    """
    The main agent node that calls the LLM for general dialogue.
    """
    messages = state["messages"]

    # Prepend System Prompt to the messages sent to the LLM
    messages_with_prompt = [SystemMessage(content=SYSTEM_PROMPT)] + messages

    response = model.invoke(messages_with_prompt, config=config)
    return {"messages": [response]}
