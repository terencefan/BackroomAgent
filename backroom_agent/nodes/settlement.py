from typing import Any, Dict

from langchain_core.runnables import RunnableConfig

from backroom_agent.state import State
from backroom_agent.utils.logger import logger
from backroom_agent.utils.node_annotation import annotate_node


@annotate_node("normal")
def settlement_node(state: State, config: RunnableConfig) -> Dict[str, Any]:
    """
    Settlement Node (Convergence):
    A pass-through node that collects flows from various resolve nodes (Event, Item, etc.)
    before passing control to the Summary Node.
    """
    logger.info("▶ NODE: Settlement Node")
    return {}
