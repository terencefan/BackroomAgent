import logging

from langchain_core.runnables import RunnableConfig

from backroom_agent.state import State
from backroom_agent.utils.common import print_debug_message

logger = logging.getLogger(__name__)


def summary_node(state: State, config: RunnableConfig) -> dict:
    """
    Summarizes the transaction and updates the final game state.
    """
    current = state.get("current_game_state")
    if current:
        # Assuming Pydantic v2 model_copy.
        # Deep copy to ensure we don't mutate the input directly before returning (though typeddict behavior varies)
        try:
            new_state = current.model_copy(deep=True)
        except AttributeError:
            new_state = current.copy(deep=True)

        # Placeholder logic: simple time increment
        new_state.time += 1

        # Log metadata about the turn
        msgs = state.get("messages", [])
        if msgs:
            last_content = msgs[-1].content
            print_debug_message(
                "Summary Node [Turn Complete]:",
                [
                    f"- Time: {new_state.time}",
                    f"- Model Output: {str(last_content)[:200]}...",
                ],
            )

        return {"current_game_state": new_state}
    return {}
