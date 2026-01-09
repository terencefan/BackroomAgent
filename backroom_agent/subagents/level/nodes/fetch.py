import logging
import os

from backroom_agent.tools.wiki_tools import (fetch_wiki_content,
                                             get_level_name_from_url)
from backroom_agent.utils.common import get_project_root
from ..state import LevelAgentState

logger = logging.getLogger(__name__)


def fetch_content_node(state: LevelAgentState):
    """
    Fetches HTML content from URL or local file.
    """
    url = state.get("url")
    level_name = state.get("level_name")
    logs = state.get("logs", [])

    html_content = ""

    # 1. Determine Level Name
    if not level_name and url:
        level_name = get_level_name_from_url(url)

    if not level_name:
        return {"logs": logs + ["Error: Could not determine level name."]}

    # 2. Check Local File first if not forcing update
    root = get_project_root()
    html_path = os.path.join(root, "data/level", f"{level_name}.html")

    if os.path.exists(html_path) and not state.get("force_update") and not url:
        # Load local
        logs.append(f"Loading local HTML for {level_name}")
        with open(html_path, "r", encoding="utf-8") as f:
            html_content = f.read()
    elif url:
        # Fetch remote
        # We reuse the existing tool logic which saves to file automatically
        logs.append(f"Fetching remote content from {url}")
        content, extracted_name = fetch_wiki_content(url, save_files=True)
        html_content = content
        if not level_name:
            level_name = extracted_name  # Update if we didn't have it
    else:
        # If still no URL here (search failed in previous node), use local check or fail
        msg = f"No URL provided and search failed for {level_name}"
        logs.append(msg)
        # Try local fallback one last time even without force check
        if os.path.exists(html_path):
            logs.append(f"Fallback: Loading local HTML for {level_name}")
            with open(html_path, "r", encoding="utf-8") as f:
                html_content = f.read()
        else:
            return {"logs": logs + [f"Error: {msg}"]}

    return {
        "html_content": html_content,
        "level_name": level_name,
        "url": url,
        "logs": logs,
    }
