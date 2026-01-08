import os
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from backroom_agent.state import State
from backroom_agent.utils.common import load_prompt, get_llm

# Singleton model instance
model = get_llm()

def _load_system_prompt() -> str:
    """Load the system prompt from the prompts directory."""
    try:
        return load_prompt("dm_agent.md")
    except FileNotFoundError:
        return "You are a helpful AI Dungeon Master for a Backrooms game."

SYSTEM_PROMPT = _load_system_prompt()

def dm_agent(state: State, config: RunnableConfig) -> dict:
    """
    The main agent node that calls the LLM.
    """
    messages = state["messages"]
    
    # Prepend System Prompt to the messages sent to the LLM
    # We do NOT add it to the state history to avoid duplication, 
    # we just use it for this inference call.
    messages_with_prompt = [SystemMessage(content=SYSTEM_PROMPT)] + messages
    
    response = model.invoke(messages_with_prompt, config=config)
    return {"messages": [response]}
