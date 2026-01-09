import logging
import os
import re
from urllib.parse import urlparse

from backroom_agent.utils.common import get_project_root
from backroom_agent.utils.search import search_backrooms_wiki
from ..state import LevelAgentState

logger = logging.getLogger(__name__)


def resolve_url_node(state: LevelAgentState):
    """
    Check if the input is a valid Backrooms URL. If not, search for it.
    Also initializes state flags.
    """
    url = state.get("url")
    level_name = state.get("level_name")
    logs = state.get("logs", [])

    # Initialize flags
    state_updates = {"items_extracted": False, "entities_extracted": False}

    # Allowed domains
    target_domains = ["backrooms-wiki-cn.wikidot.com", "brcn.backroomswiki.cn"]

    # 1. Check if we already have a URL
    if url:
        parsed = urlparse(url)
        if any(domain in parsed.netloc for domain in target_domains):
            logs.append(f"Valid URL provided: {url}")
            state_updates["logs"] = logs
            return state_updates
        else:

            # URL provided but not in allowed list?
            # It might be a search term passed as URL or just an external link.
            # If it's not a URL structure at all, treat as search term.
            if not parsed.scheme:
                # User likely passed "Level 1" into the url field
                logs.append(f"Input '{url}' is not a URL. Using as search query.")
                level_name = url  # Treat input as level name query
                url = None
            else:
                logs.append(
                    f"Warning: URL {url} is not from allowed domains. Attempting to use anyway or search."
                )

    # 2. Check for local file first to avoid unnecessary search
    if not url and level_name:
        root = get_project_root()
        # Try both original and normalized name
        candidates = [level_name, level_name.lower().replace(" ", "-")]
        for cand in candidates:
            html_path = os.path.join(root, "data/level", f"{cand}.html")
            if os.path.exists(html_path):
                logs.append(
                    f"Found local file for {level_name} at {html_path}. Skipping search."
                )
                state_updates["logs"] = logs
                state_updates["level_name"] = cand
                return state_updates

    # 3. If no valid URL and no local file, try to construct standard URL or search
    if not url and level_name:
        # Heuristic: If it looks like a standard numbered level, construct URL directly
        # Matches: "Level 12", "level-12", "Level-12", "12" (maybe too risky?)
        normalized_name = level_name.lower().replace(" ", "-")
        params_pattern = re.compile(r"^level-\d+$")
        
        if params_pattern.match(normalized_name):
            constructed_url = f"https://backrooms-wiki-cn.wikidot.com/{normalized_name}"
            logs.append(f"Detected standard level format. Using constructed URL: {constructed_url}")
            state_updates["logs"] = logs
            state_updates["url"] = constructed_url
            return state_updates

        # Otherwise, search
        logs.append(f"Searching for wiki page: {level_name}")
        found_url = search_backrooms_wiki(level_name)
        if found_url:
            logs.append(f"Found URL: {found_url}")
            state_updates["logs"] = logs
            state_updates["url"] = found_url
            return state_updates
        
        # Fallback: Construct URL if search failed
        fallback_url = f"https://backrooms-wiki-cn.wikidot.com/{normalized_name}"
        logs.append(f"Search failed. Attempting fallback URL: {fallback_url}")
        state_updates["url"] = fallback_url
        state_updates["logs"] = logs
        return state_updates

    state_updates["logs"] = logs
    return state_updates
