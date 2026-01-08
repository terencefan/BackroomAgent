from typing import List

from langchain_core.runnables import RunnableConfig

from backroom_agent.state import State


def suggestion_node(state: State, config: RunnableConfig) -> dict:
    """
    Generates suggestions for the player's next actions.
    """
    # Simple rule-based suggestions for now. 
    # Can be upgraded to LLM-based later.
    default_suggestions = ["Look around", "Check status", "Wait"]
    
    return {"suggestions": default_suggestions}
