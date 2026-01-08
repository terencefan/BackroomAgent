import glob
import json
import logging
import os
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

# Assumes this file is in backroom_agent/utils/level.py
# data/level is at ../../data/level relative to this file
LEVEL_DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../data/level"))


def find_level_data(target_level_id: str) -> Tuple[Optional[Dict], Optional[str]]:
    """
    Searches for a JSON file in data/level where the 'level_id' field matches target_level_id.
    Returns the parsed JSON data and the content of the corresponding .html file.
    
    :param target_level_id: The ID to search for (e.g., "Level 0")
    :return: (json_data, html_content) or (None, None) if not found.
    """
    if not os.path.exists(LEVEL_DATA_DIR):
        logger.error(f"Level data directory not found at: {LEVEL_DATA_DIR}")
        return None, None

    logger.info(f"Searching for level data for ID: '{target_level_id}' in {LEVEL_DATA_DIR}")

    # Optimization: Try to guess the filename first (e.g., "Level 0" -> "level-0.json")
    # This is just a heuristic fast path.
    guessed_filename = target_level_id.lower().replace(" ", "-") + ".json"
    guessed_path = os.path.join(LEVEL_DATA_DIR, guessed_filename)
    
    if os.path.exists(guessed_path):
        try:
            with open(guessed_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("level_id") == target_level_id:
                return _load_pair(guessed_path, data)
        except Exception:
            # Fallback to full scan if read fails or ID doesn't match
            pass

    # Full scan
    pattern = os.path.join(LEVEL_DATA_DIR, "*.json")
    for file_path in glob.glob(pattern):
        # Skip the guessed path if we already checked it
        if file_path == guessed_path:
            continue
            
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            if data.get("level_id") == target_level_id:
                return _load_pair(file_path, data)
                
        except json.JSONDecodeError:
            logger.warning(f"Failed to parse JSON: {file_path}")
        except Exception as e:
            logger.warning(f"Error reading {file_path}: {e}")

    logger.warning(f"No level data found for ID: {target_level_id}")
    return None, None


def _load_pair(json_path: str, json_data: Dict) -> Tuple[Dict, Optional[str]]:
    """Helper to load the HTML file corresponding to a JSON file."""
    html_path = json_path.replace(".json", ".html")
    html_content = None
    
    if os.path.exists(html_path):
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
        except Exception as e:
            logger.error(f"Failed to read HTML file {html_path}: {e}")
    else:
        logger.warning(f"Corresponding HTML file not found: {html_path}")

    return json_data, html_content
