import logging
from typing import List

from langchain_core.runnables import RunnableConfig

from backroom_agent.state import State
from backroom_agent.subagents.suggestion import suggestion_agent

logger = logging.getLogger(__name__)


async def suggestion_node(state: State, config: RunnableConfig) -> dict:
    """
    Generates suggestions for the player's next actions.
    """
    logger.info("Invoking Suggestion Sub-Agent...")

    # Invoke the sub-agent with shared state
    # Since they share the same schema, we can pass state directly
    result = await suggestion_agent.ainvoke(state)

    suggestions = result.get("suggestions", [])
    if not suggestions:
        suggestions = ["Look around", "Check inventory"]

    return {"suggestions": suggestions}
