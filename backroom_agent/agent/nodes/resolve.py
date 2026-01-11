from typing import Any, Dict

from langchain_core.runnables import RunnableConfig

from backroom_agent.constants import NodeConstants
from backroom_agent.agent.state import State
from backroom_agent.utils.logger import logger
from backroom_agent.utils.node_annotation import annotate_node


def route_resolve(state: State) -> str:
    """
    Determines the next step after Resolve Node.
    - If suggestions exist: Proceed to Summary (End of Turn).
    - If no suggestions: Loop back to Event Node to generate them (or continue narrative).
    """
    suggestions = state.get("suggestions")
    if suggestions and len(suggestions) > 0:
        return NodeConstants.SUMMARY_NODE

    # Safety: prevent infinite loops if LLM refuses to generate suggestions
    loop_count = state.get("turn_loop_count", 0)
    if loop_count > 5:
        logger.warning(
            "Max loops reached in Resolve Routing without suggestions. Forcing exit."
        )
        return NodeConstants.SUMMARY_NODE

    return NodeConstants.EVENT_NODE


@annotate_node("normal")
def resolve_node(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """
    Resolve Node (formerly Settlement/EventResolve):
    Finalizes the turn.
    Since 'issuing suggestions' is logically moved here, we ensure
    we are ready to transition to Summary if suggestions are present.
    """
    logger.info("▶ NODE: Resolve Node")
    return {}
