import json
import logging
import os

from langchain_core.messages import HumanMessage, SystemMessage

from backroom_agent.utils.common import get_llm, get_project_root, load_prompt

from .state import LevelAgentState

logger = logging.getLogger(__name__)


def generate_json_node(state: LevelAgentState):
    """
    Generates the Level JSON description from HTML using an LLM.
    """
    html_content = state.get("html_content")
    level_name = state.get("level_name")
    logs = state.get("logs", [])

    if not html_content:
        return {"logs": logs + ["Skipping JSON generation: No HTML content."]}

    # Check if JSON already exists
    root = get_project_root()
    json_path = os.path.join(root, "data/level", f"{level_name}.json")

    if os.path.exists(json_path) and not state.get("force_update"):
        logs.append(f"JSON already exists at {json_path}. Skipping generation.")
        return {"level_json_generated": True, "logs": logs}

    logs.append("Generating Level JSON from HTML...")
    try:
        # LLM Generation logic
        llm = get_llm()
        prompt_path = os.path.join(
            os.path.dirname(__file__), "prompts", "generate_json.prompt"
        )
        system_prompt_text = load_prompt(prompt_path)

        messages = [
            SystemMessage(content=system_prompt_text),
            HumanMessage(
                content=f"Here is the cleaned HTML content of the level:\n\n{html_content}"
            ),
        ]

        response = llm.invoke(messages)
        content = response.content

        # Clean up markdown code blocks
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()

        # Save the generated JSON
        os.makedirs(os.path.dirname(json_path), exist_ok=True)
        with open(json_path, "w", encoding="utf-8") as f:
            f.write(content)

        logs.append(f"Successfully generated and saved {json_path}")
        return {"level_json_generated": True, "logs": logs}
    except Exception as e:
        logs.append(f"Error generating JSON: {str(e)}")
        return {"level_json_generated": False, "logs": logs}


def extract_items_node(state: LevelAgentState):
    """
    Extracts potential items from the HTML content using LLM.
    """
    html_content = state.get("html_content")
    logs = state.get("logs", [])

    if not html_content:
        return {"extracted_items_raw": [], "logs": logs}

    logs.append("Extracting items from HTML...")

    llm = get_llm()
    prompt_path = os.path.join(
        os.path.dirname(__file__), "prompts", "extract_items.prompt"
    )
    system_prompt = load_prompt(prompt_path)

    # We might want to truncate HTML if it's too long, but usually wiki pages are okay for recent models
    messages = [
        SystemMessage(content=system_prompt.format(context=html_content)),
        HumanMessage(content="Extract the items now in JSON format."),
    ]

    try:
        response = llm.invoke(messages)
        content = response.content

        # Parse JSON from Markdown block
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()

        parsed_json = json.loads(content)

        # Handle new format {"findable_items": [...]} or old list format
        if isinstance(parsed_json, dict) and "findable_items" in parsed_json:
            items = parsed_json["findable_items"]
        elif isinstance(parsed_json, list):
            items = parsed_json
        else:
            items = []
            logs.append(
                f"Warning: Unexpected JSON format. Got keys: {parsed_json.keys() if isinstance(parsed_json, dict) else 'Not a dict'}"
            )

        logs.append(f"Extracted {len(items)} raw items.")
        return {"extracted_items_raw": items, "logs": logs}

    except Exception as e:
        logs.append(f"Error extracting items: {e}")
        return {"extracted_items_raw": [], "logs": logs}


def extract_entities_node(state: LevelAgentState):
    """
    Extracts potential entities from the HTML content using LLM.
    """
    html_content = state.get("html_content")
    logs = state.get("logs", [])

    if not html_content:
        return {"extracted_entities_raw": [], "logs": logs}

    logs.append("Extracting entities from HTML...")

    llm = get_llm()
    prompt_path = os.path.join(
        os.path.dirname(__file__), "prompts", "extract_entities.prompt"
    )
    system_prompt = load_prompt(prompt_path)

    messages = [
        SystemMessage(content=system_prompt.format(context=html_content)),
        HumanMessage(content="Extract the entities now in JSON format."),
    ]

    try:
        response = llm.invoke(messages)
        content = response.content

        # Parse JSON from Markdown block
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].strip()

        parsed_json = json.loads(content)

        if isinstance(parsed_json, dict) and "entities" in parsed_json:
            entities = parsed_json["entities"]
        else:
            entities = []
            logs.append(
                f"Warning: Unexpected JSON format for entities. Got keys: {parsed_json.keys() if isinstance(parsed_json, dict) else 'Not a dict'}"
            )

        logs.append(f"Extracted {len(entities)} raw entities.")
        return {"extracted_entities_raw": entities, "logs": logs}

    except Exception as e:
        logs.append(f"Error extracting entities: {e}")
        return {"extracted_entities_raw": [], "logs": logs}
