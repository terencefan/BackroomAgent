import os

from langchain_core.messages import SystemMessage

from backroom_agent.utils.common import get_llm, load_prompt
from backroom_agent.utils.logger import logger

from .state import EventAgentState


def generate_event_node(state: EventAgentState):
    """
    Generates a random event based on current context.
    """
    logger.info("Event Agent: Generating event...")

    current_level = state.get("current_level", "Unknown Level")
    player_status = state.get("player_status", "Normal")

    # Load system prompt
    prompt_path = os.path.join(
        os.path.dirname(__file__), "prompts", "event_agent.prompt"
    )
    system_prompt_template = load_prompt(prompt_path)
    if not system_prompt_template:
        system_prompt_template = (
            "You are an event generator for the Backrooms. Create a spooky event."
        )

    system_message = SystemMessage(
        content=system_prompt_template.format(
            current_level=current_level, player_status=player_status
        )
    )

    messages = [system_message] + state["messages"]

    llm = get_llm()
    response = llm.invoke(messages)

    return {"event_result": response.content}
