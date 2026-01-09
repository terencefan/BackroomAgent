import json
import os
import re

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from backroom_agent.constants import API_KEY, BASE_URL, MODEL_NAME


def get_project_root() -> str:
    """Returns the absolute path to the project root directory."""
    # current file: backroom_agent/utils/__init__.py or common.py
    # Assuming this file is at backroom_agent/utils/common.py
    # and project root is two levels up from backroom_agent

    # Path of this file: .../backroom_agent/utils/common.py
    current_dir = os.path.dirname(os.path.abspath(__file__))

    # Parent of utils: .../backroom_agent
    backroom_agent_dir = os.path.dirname(current_dir)

    # Parent of backroom_agent: .../ProjectRoot
    project_root = os.path.dirname(backroom_agent_dir)

    return project_root


def load_prompt(file_path: str) -> str:
    """Loads the content of a prompt file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()


def get_llm() -> BaseChatModel:
    """Return a chat model based on configuration."""
    if not API_KEY:
        raise ValueError("API_KEY is missing. Please check your .env file.")

    return ChatOpenAI(api_key=API_KEY, base_url=BASE_URL, model=MODEL_NAME)  # type: ignore


def print_debug_message(title: str, content: list[str] | str):
    """Prints a formatted debug message to the console."""
    print("-" * 30)
    print(f"DEBUG: {title}")

    if isinstance(content, list):
        for line in content:
            print(line)
    else:
        print(content)

    print("-" * 30)


def save_to_file(content: str, directory: str, filename: str):
    """Saves content to a file in the specified directory."""
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return filepath


def extract_json_from_text(text: str) -> dict:
    """
    Attempts to parse JSON from text using multiple strategies.

    Strategies:
    1. Direct json.loads
    2. Extract from markdown code blocks (```json ... ```)
    3. Extract from outermost curly braces

    Args:
        text (str): The raw text potentially containing JSON.

    Returns:
        dict: The parsed JSON object.

    Raises:
        json.JSONDecodeError: If JSON cannot be extracted/parsed.
    """
    # Strategy 1: Direct Parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Markdown Code Blocks
    # Matches ```json {content} ``` or ``` {content} ```
    pattern = r"```(?:json)?\s*([\s\S]*?)\s*```"
    match = re.search(pattern, text)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: Outermost Braces
    # Finds the first '{' and last '}'
    try:
        start_idx = text.find("{")
        end_idx = text.rfind("}")

        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            json_str = text[start_idx : end_idx + 1]
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # If all fail, re-raise the original error (or a generic one)
    raise json.JSONDecodeError("Failed to extract valid JSON from text", text, 0)
