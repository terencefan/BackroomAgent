import json
import os
import re
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from backroom_agent.constants import (DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL,
                                      DEEPSEEK_MODEL, DOUBAO_API_KEY,
                                      DOUBAO_BASE_URL, DOUBAO_MODEL,
                                      OPENAI_API_KEY)
from backroom_agent.utils.logger import logger


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


def dict_from_pydantic(model: Any) -> dict:
    """
    Safely converts a Pydantic model to a dictionary.
    Supports Pydantic V2 (`model_dump`) and V1 (`dict`).
    """
    try:
        return model.model_dump()
    except AttributeError:
        return model.dict()


def get_llm(provider: str = "deepseek") -> BaseChatModel:
    """
    Return a chat model based on the specified provider.

    Args:
        provider: Provider name ("deepseek" or "doubao"). Default: "deepseek".

    Returns:
        BaseChatModel: Configured chat model instance.

    Raises:
        ValueError: If API key is missing for the specified provider or provider is invalid.

    Examples:
        >>> # Use deepseek (default)
        >>> llm = get_llm("deepseek")
        >>> # or simply
        >>> llm = get_llm()

        >>> # Use doubao
        >>> llm = get_llm("doubao")
    """
    selected_provider = provider.lower()

    if selected_provider == "deepseek":
        api_key = DEEPSEEK_API_KEY or OPENAI_API_KEY
        base_url = DEEPSEEK_BASE_URL
        model_name = DEEPSEEK_MODEL
        provider_display = "DeepSeek"
    elif selected_provider == "doubao":
        api_key = DOUBAO_API_KEY or OPENAI_API_KEY
        base_url = DOUBAO_BASE_URL
        model_name = DOUBAO_MODEL
        provider_display = "Doubao"
    else:
        raise ValueError(
            f"Invalid provider '{provider}'. Supported providers: 'deepseek', 'doubao'"
        )

    if not api_key:
        raise ValueError(
            f"{provider_display} API key is missing. "
            f"Please set {selected_provider.upper()}_API_KEY in your .env file, "
            "or set OPENAI_API_KEY as fallback."
        )

    return ChatOpenAI(api_key=api_key, base_url=base_url, model=model_name)  # type: ignore


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
    # Matches ```json {content} ``` or ``` {content} ``` or ```xml...
    # Improved regex to capture any language identifier
    pattern = r"```(?:\w+)?\s*([\s\S]*?)\s*```"
    matches = re.finditer(pattern, text)
    for match in matches:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            continue

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

    # Strategy 4: Aggressive Cleaning (Fallback)
    # Sometimes 'json' is written without backticks but with a label
    # or obscure markdown characters.
    try:
        # Remove common markdown fence markers manually
        cleaned = text.replace("```json", "").replace("```", "").strip()
        # Find braces again in cleaned text
        start_idx = cleaned.find("{")
        end_idx = cleaned.rfind("}")
        if start_idx != -1 and end_idx != -1 and start_idx < end_idx:
            json_str = cleaned[start_idx : end_idx + 1]
            # Extra Step: Fix invalid "+5" number formats common in LLM outputs
            # Matches : +5, [ +5, , +5
            json_str = re.sub(r"([:\[,])(\s*)\+(\d+)", r"\1\2\3", json_str)
            return json.loads(json_str)
    except json.JSONDecodeError:
        pass

    # If all fail, re-raise the original error (or a generic one)
    raise json.JSONDecodeError("Failed to extract valid JSON from text", text, 0)


def truncate_text(text: str, length: int = 50, suffix: str = "...") -> str:
    """
    Truncates text to a specified length, adding a suffix only if truncated.

    Args:
        text: The string to truncate.
        length: The maximum length desired (including suffix if strictly enforced,
                but usually interpreted as content length before truncation).
                Here it means: keep first `length` characters.
        suffix: String to append if text is truncated.

    Returns:
        The truncated string with suffix if needed.
    """
    if len(text) <= length:
        return text
    return text[:length] + suffix
