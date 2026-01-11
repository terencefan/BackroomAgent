import json
import os
import re

from langchain_core.messages import SystemMessage

from backroom_agent.agent.state import State
from backroom_agent.utils.common import get_llm, load_prompt
from backroom_agent.utils.logger import logger
from backroom_agent.utils.node_annotation import annotate_node


@annotate_node("llm")
def generate_suggestions_node(state: State):
    """
    Generates action suggestions for the player.
    """
    logger.info("Suggestion Agent: Thinking...")

    current_context = state.get("level_context", "")
    valid_actions = state.get("valid_actions", []) or []

    prompt_path = os.path.join(
        os.path.dirname(__file__), "prompts", "suggestion_agent.prompt"
    )
    system_prompt_template = load_prompt(prompt_path)
    if not system_prompt_template:
        system_prompt_template = (
            "Suggest 3 reasonable actions for the player in a text adventure game."
        )

    system_message = SystemMessage(
        content=system_prompt_template.format(
            current_context=current_context, valid_actions=", ".join(valid_actions)
        )
    )

    messages = [system_message] + state["messages"]

    llm = get_llm()
    response = llm.invoke(messages)

    content = response.content
    if not isinstance(content, str):
        content = str(content)
    content = content.strip()
    suggestions = []

    # Clean up markdown code blocks if present
    content = re.sub(r"^```json\s*", "", content)
    content = re.sub(r"^```\s*", "", content)
    content = re.sub(r"\s*```$", "", content)

    try:
        parsed = json.loads(content)
        if isinstance(parsed, list):
            suggestions = [
                str(s).strip() for s in parsed if isinstance(s, (str, int, float))
            ]
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse suggestions JSON: {content}")
        # Fallback to simple split if JSON fails
        suggestions = [
            line.strip("- *\"'") for line in content.split("\n") if line.strip()
        ][:3]

    # Final cleanup (just in case)
    suggestions = [s for s in suggestions if s]

    # Fallback if empty
    if not suggestions:
        suggestions = ["环顾四周", "检查背包"]

    return {"suggestions": suggestions}
