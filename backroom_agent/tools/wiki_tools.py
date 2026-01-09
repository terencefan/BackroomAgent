import os

from langchain_core.messages import HumanMessage, SystemMessage
from langsmith import traceable

# Import from new refactored modules
from backroom_agent.tools.wiki.fetch import (fetch_url_content,
                                             get_level_name_from_url)
from backroom_agent.tools.wiki.parse import clean_html_content
from backroom_agent.utils.common import (get_llm, get_project_root,
                                         load_prompt, save_to_file)


@traceable(run_type="chain", name="Convert HTML to Room JSON")
def convert_html_to_room_json(html_content: str, level_name: str) -> str:
    """
    Converts cleaned HTML content to a Game Context JSON using an LLM.

    Args:
        html_content (str): The cleaned HTML content.
        level_name (str): The name/ID of the level for saving the file.

    Returns:
        str: A JSON string representing the game context.
    """
    root_dir = get_project_root()
    json_path = os.path.join(root_dir, "data/level", f"{level_name}.json")

    llm = get_llm()
    prompt_path = os.path.join(
        root_dir, "backroom_agent/subagents/level/prompts/generate_json.prompt"
    )
    system_prompt_text = load_prompt(prompt_path)

    messages = [
        SystemMessage(content=system_prompt_text),
        HumanMessage(
            content=f"Here is the cleaned HTML content of the level:\n\n{html_content}"
        ),
    ]

    # We can try to use standard invoke. The prompt asks for a Markdown code block with JSON.
    response = llm.invoke(messages)
    content = response.content

    # Helper to clean up markdown code blocks if present
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].strip()

    # Save the generated JSON
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(content)

    return content


@traceable(run_type="tool", name="Fetch Wiki Content")
def fetch_wiki_content(
    url: str, save_files: bool = True
) -> tuple[str | None, str | None]:
    """
    Fetches the content of a URL and cleans it, keeping only useful tags.
    Saves raw content to data/raw and cleaned content to data/level.

    Args:
        url (str): The URL to fetch.
        save_files (bool): Whether to save the raw and cleaned content to files.

    Returns:
        tuple[str | None, str | None]: The cleaned HTML content string and the Level Name.
    """
    raw_content = fetch_url_content(url)

    if not raw_content:
        return None, None

    level_name = get_level_name_from_url(url)
    root_dir = get_project_root()

    if save_files:
        save_to_file(
            raw_content, os.path.join(root_dir, "data/raw"), f"{level_name}.html"
        )

    cleaned_content = clean_html_content(raw_content)

    # Post-process cleaning (normalize newlines)
    cleaned_content = "\n".join(
        [line.strip() for line in cleaned_content.splitlines() if line.strip()]
    )

    if save_files:
        save_to_file(
            cleaned_content, os.path.join(root_dir, "data/level"), f"{level_name}.html"
        )

    return cleaned_content, level_name
