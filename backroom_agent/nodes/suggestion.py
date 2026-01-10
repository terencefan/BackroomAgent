from typing import Any, List, cast

from langchain_core.runnables import RunnableConfig

from backroom_agent.state import State
from backroom_agent.subagents.suggestion import suggestion_agent
from backroom_agent.utils.logger import logger
from backroom_agent.utils.node_annotation import annotate_node


@annotate_node("llm")
async def suggestion_node(state: State, config: RunnableConfig) -> dict:
    """
    Generates suggestions for the player's next actions.
    """
    logger.info("▶ NODE: Suggestion Node")

    # Invoke the sub-agent with shared state
    # Since they share the same schema, we can pass state directly
    # Cast State to Any to bypass MyPy TypedDict vs Dict mismatch in LangGraph compiled graph
    result = await suggestion_agent.ainvoke(cast(Any, state))

    suggestions = result.get("suggestions", [])
    if not suggestions:
        suggestions = ["Look around", "Check inventory"]

    return {"suggestions": suggestions}
