from typing import Any, Dict

from langchain_core.runnables import RunnableConfig

from backroom_agent.state import State
from backroom_agent.utils.logger import logger
from backroom_agent.utils.node_annotation import annotate_node


@annotate_node("normal")
def resolve_node(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """
    Resolve Node (formerly Settlement/EventResolve):
    Finalizes the turn. Since we skipped Dice, there are no specific mechanics to apply here
    (unless we add cleanup logic later).
    This node acts as the convergence point before Summary.
    """
    logger.info("▶ NODE: Resolve Node")
    return {}
