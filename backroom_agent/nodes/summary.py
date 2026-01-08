from langchain_core.runnables import RunnableConfig

from backroom_agent.state import State


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
        
        return {"current_game_state": new_state}
    return {}
