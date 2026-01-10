from langchain_core.messages import AIMessage
from langchain_core.runnables import RunnableConfig

from backroom_agent.protocol import EventType
from backroom_agent.state import State
from backroom_agent.utils.logger import logger
from backroom_agent.utils.node_annotation import annotate_node


@annotate_node("normal")
def item_node(state: State, config: RunnableConfig) -> dict:
    """Handles item usage and dropping."""
    logger.info("▶ NODE: Item Node")

    event = state.get("event")
    item_id = event.item_id if event else "unknown"
    quantity = event.quantity or 1
    event_type = event.type if event else EventType.USE

    action = "used" if event_type == EventType.USE else "dropped"
    msg = f"You {action} {quantity}x {item_id}. (Logic placeholder)"

    return {"messages": [AIMessage(content=msg)]}
