import logging
import os
from langchain_core.messages import SystemMessage
from backroom_agent.utils.common import load_prompt, get_llm
from .state import SuggestionAgentState

logger = logging.getLogger(__name__)

def generate_suggestions_node(state: SuggestionAgentState):
    """
    Generates action suggestions for the player.
    """
    logger.info("Suggestion Agent: Thinking...")
    
    current_context = state.get("current_context", "")
    valid_actions = state.get("valid_actions", [])
    
    prompt_path = os.path.join(os.path.dirname(__file__), "prompts", "suggestion_agent.prompt")
    system_prompt_template = load_prompt(prompt_path)
    if not system_prompt_template:
        system_prompt_template = "Suggest 3 reasonable actions for the player in a text adventure game."
        
    system_message = SystemMessage(content=system_prompt_template.format(
        current_context=current_context,
        valid_actions=", ".join(valid_actions)
    ))
    
    messages = [system_message] + state["messages"]
    
    llm = get_llm()
    response = llm.invoke(messages)
    
    # Simple parsing assuming the LLM returns a numbered list or just lines
    # Ideally we'd ask for JSON, but let's keep it simple for now matching the prompt
    content = response.content
    suggestions = [line.strip() for line in content.split('\n') if line.strip() and (line[0].isdigit() or line.startswith('-'))]
    
    # Fallback if parsing fails
    if not suggestions:
        suggestions = [content]

    return {"suggestions": suggestions}
