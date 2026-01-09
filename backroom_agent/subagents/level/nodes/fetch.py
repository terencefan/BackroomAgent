import logging
import os
import re
from typing import Dict, List, Optional, Tuple
from urllib.parse import urlparse

from backroom_agent.tools.wiki.parse import \
    clean_html_content  # Import cleaning logic
from backroom_agent.tools.wiki_tools import (fetch_wiki_content,
                                             get_level_name_from_url)
from backroom_agent.utils.common import get_project_root
from backroom_agent.utils.search import search_backrooms_wiki

from ..state import LevelAgentState

logger = logging.getLogger(__name__)

# --- Domain Priority Configuration ---
# Ordered by priority (first is preferred)
WIKI_MIRRORS = [
    "http://brcn.backroomswiki.cn",
    "https://backrooms-wiki-cn.wikidot.com",
]


def _get_allowed_domains() -> List[str]:
    return [urlparse(m).netloc for m in WIKI_MIRRORS]


def _try_load_raw_and_clean(
    level_name: Optional[str], url: Optional[str], logs: List[str]
) -> Tuple[Optional[str], Optional[str], List[Dict[str, str]]]:
    """
    Fallback method: Try to load from data/raw/ and apply NEW cleaning logic.
    Useful when network is down but we want to re-process cached raw data.
    """
    root = get_project_root()
    candidates = []

    # 1. From level_name
    if level_name:
        candidates.append(level_name)
        candidates.append(level_name.lower().replace(" ", "-"))

    # 2. From URL (extract name if possible)
    if url:
        extracted = get_level_name_from_url(url)
        if extracted:
            candidates.append(extracted)

    for cand in candidates:
        raw_path = os.path.join(root, "data/raw", f"{cand}.html")
        if os.path.exists(raw_path):
            logs.append(f"Found RAW cache for {cand}. Cleaning and loading...")
            try:
                with open(raw_path, "r", encoding="utf-8") as f:
                    raw_content = f.read()

                # Apply Cleaning
                cleaned_content, extracted_links = clean_html_content(raw_content)
                cleaned_content = "\n".join(
                    [
                        line.strip()
                        for line in cleaned_content.splitlines()
                        if line.strip()
                    ]
                )

                # Optional: Update the data/level/ file too?
                # Yes, if we are 'forcing' update from raw, we should update the cleaned cache.
                clean_path = os.path.join(root, "data/level", f"{cand}.html")
                with open(clean_path, "w", encoding="utf-8") as f:
                    f.write(cleaned_content)

                return cleaned_content, cand, extracted_links
            except Exception as e:
                logs.append(f"Failed to process raw file: {e}")

    return None, None, []


def _get_mirror_url(path_segment: str, mirror_base: str) -> str:
    """Combines a mirror base URL with a path segment."""
    return f"{mirror_base.rstrip('/')}/{path_segment.lstrip('/')}"


def _generate_alternatives(url: str) -> List[str]:
    """
    Given a URL, generates a list of alternative URLs on other mirrors.
    The list starts with the provided URL's domain equivalent (if in list),
    followed by others in priority order.
    """
    parsed = urlparse(url)
    path = parsed.path
    if not path or path == "/":
        return []

    alternatives = []
    # If the input URL matches one of our mirrors, start with it (or its priority equivalent?)
    # Users Logic: "Priority System".
    # Approach:
    # 1. Identify valid path from the URL.
    # 2. Return list of ALL mirrors with that path, in WIKI_MIRRORS order.

    # Check if current URL is in our mirrors list
    current_netloc = parsed.netloc
    allowed = _get_allowed_domains()

    # If URL is external/unknown, we can't safely assume path compatibility,
    # but for this specific wiki ecosystem, we often can.
    # Let's assume the path is portable.

    for base in WIKI_MIRRORS:
        alt = _get_mirror_url(path, base)
        # Avoid exact duplicates of the input url if needed,
        # but pure reconstruction ensures cleanliness.
        if alt not in alternatives:
            alternatives.append(alt)

    # If the original URL was NOT in our standard mirrors, maybe we should keep it
    # as a fallback or primary?
    # If it came from search, it might be unique.
    # Let's ensure the original URL is in the list if it wasn't covered.
    cleaned_original = url.rstrip("/")
    if cleaned_original not in alternatives and current_netloc not in allowed:
        # If it's a completely different domain, maybe we shouldn't try mirrors unless we trust path?
        # But the request implies managing *our* domains.
        # So: Try our mirrors (priority) + Original (if untrusted).
        pass

    return alternatives


def _normalize_input(
    url: Optional[str], level_name: Optional[str], logs: List[str]
) -> Tuple[Optional[str], Optional[str]]:
    """
    Step 1: Normalize input.
    Checks if the provided URL is valid or matches known domains.
    If 'url' looks like a search query, moves it to 'level_name'.
    """
    target_domains = _get_allowed_domains()

    if url:
        parsed = urlparse(url)
        if any(domain in parsed.netloc for domain in target_domains):
            logs.append(f"Valid URL provided (matches allowed domain): {url}")
        elif not parsed.scheme:
            logs.append(f"Input '{url}' is not a URL. Using as level_name.")
            # If no level_name was provided, use the url as level_name
            if not level_name:
                level_name = url
            url = None
        else:
            logs.append(f"Warning: URL {url} is not from allowlisted domains.")

    return url, level_name


def _try_load_local(
    level_name: Optional[str], url: Optional[str], logs: List[str]
) -> Tuple[Optional[str], Optional[str]]:
    """
    Step 2: Try to find a local HTML file for the level.
    Returns (html_content, valid_level_name) if found, else (None, None).
    """
    root = get_project_root()
    candidates = []

    # 1. From level_name
    if level_name:
        candidates.append(level_name)
        candidates.append(level_name.lower().replace(" ", "-"))

    # 2. From URL (extract name if possible)
    if url and not level_name:
        extracted = get_level_name_from_url(url)
        if extracted:
            candidates.append(extracted)

    # 3. Check file existence
    for cand in candidates:
        # Check both exact match and sanitized filename
        path = os.path.join(root, "data/level", f"{cand}.html")
        if os.path.exists(path):
            logs.append(f"Found local file for {cand}. Loading...")
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return f.read(), cand
            except Exception as e:
                logs.append(f"Failed to read local file: {e}")

    return None, None


def _resolve_missing_url(level_name: str, logs: List[str]) -> str:
    """
    Step 3: If no URL is present, attempt to find one.
    Strategy:
    1. Heuristic construction (standard levels).
    2. Search.

    Returns a single 'primary' URL candidate.
    """
    normalized_name = level_name.lower().replace(" ", "-")
    params_pattern = re.compile(r"^level-\d+$")

    # Priority 0 is our preferred default
    preferred_base = WIKI_MIRRORS[0]

    # Heuristic: Standard numbered levels
    if params_pattern.match(normalized_name):
        url = _get_mirror_url(normalized_name, preferred_base)
        logs.append(f"Constructed URL (Heuristic): {url}")
        return url

    # Search
    logs.append(f"Searching for: {level_name}")
    found = search_backrooms_wiki(level_name)
    if found:
        # If search result is on a known mirror, rewrite to preferred mirror IF path is compatible?
        # Safe strategy: If successful search, trust it as the primary.
        # But we can try to optimize it.
        # Check if the found domain is in our list
        parsed = urlparse(found)
        allowed = _get_allowed_domains()

        if parsed.netloc in allowed:
            # If it's a known domain, we can try to force it to our #1 priority domain
            # just to be consistent, since _generate_alternatives will handle retries.
            # But search result might have a specific path we prefer to preserve.
            # Let's clean it and prioritize our top mirror.
            path = parsed.path
            rewritten = _get_mirror_url(path, preferred_base)
            logs.append(f"Found {found}. Rewriting to preferred: {rewritten}")
            return rewritten

        logs.append(f"Found URL via search (External/Unknown): {found}")
        return found

    # Fallback
    fallback_url = _get_mirror_url(normalized_name, preferred_base)
    logs.append(f"Search failed. Fallback to: {fallback_url}")
    return fallback_url


def fetch_content_node(state: LevelAgentState):
    """
    Resolves URL (if needed) and fetches HTML content (local or remote).
    Combines previous resolve_url_node and fetch_content_node.
    """
    url = state.get("url")
    level_name = state.get("level_name")
    logs = state.get("logs", [])
    force_update = state.get("force_update", False)

    state_updates = {
        "items_extracted": False,
        "entities_extracted": False,
        "logs": logs,
    }

    # 1. Normalize Input
    url, level_name = _normalize_input(url, level_name, logs)

    # 2. Try Local Load (if not forcing update)
    if not force_update:
        html_content, found_name = _try_load_local(level_name, url, logs)
        if html_content:
            state_updates["html_content"] = html_content
            state_updates["level_name"] = found_name or level_name
            # If we found it locally, we technically don't need the URL in state to proceed,
            # but usually good to keep what we have.
            if url:
                state_updates["url"] = url
            return state_updates

    # 3. Resolve URL (if missing)
    if not url:
        if not level_name:
            logs.append("Error: No URL and no Level Name provided.")
            return {"logs": logs}

        url = _resolve_missing_url(level_name, logs)
        state_updates["url"] = url
    else:
        # Ensure URL is passed through if it existed
        state_updates["url"] = url

    # 4. Fetch Remote
    if url:
        logs.append(f"Fetching remote content from {url}")

        # Generate candidates: [url, alt1, alt2...] or [prio1, prio2...] if url is cleaner?
        # If the input URL is from a known mirror, we should generate alternatives from it.
        # If it's external, we only try it.
        candidates = []
        is_known = any(d in url for d in _get_allowed_domains())

        if is_known:
            candidates = _generate_alternatives(url)
        else:
            candidates = [url]

        success = False
        last_error = None

        for cand in candidates:
            try:
                logs.append(f"Attempting fetch from: {cand}")
                content, extracted_name, extracted_links = fetch_wiki_content(
                    cand, save_files=True
                )

                state_updates["html_content"] = content
                state_updates["extracted_links"] = extracted_links
                state_updates["url"] = cand  # Update state with the working URL

                if not state_updates.get("level_name") and extracted_name:
                    state_updates["level_name"] = extracted_name
                elif level_name and not state.get("level_name"):
                    state_updates["level_name"] = extracted_name

                success = True
                break  # Stop on success
            except Exception as e:
                logs.append(f"Failed to fetch {cand}: {e}")
                last_error = e

        if not success:
            logs.append(f"All fetch attempts failed. Last error: {last_error}")

            # 5. Fallback to RAW cache if fetch failed
            if force_update:
                logs.append(
                    "Attempting fallback to local RAW cache due to fetch failure..."
                )
                html_content, found_name, extracted_links = _try_load_raw_and_clean(
                    level_name, url, logs
                )
                if html_content:
                    state_updates["html_content"] = html_content
                    state_updates["extracted_links"] = extracted_links
                    # Don't update URL to represent cache, keep the target URL
                    if not state_updates.get("level_name"):
                        state_updates["level_name"] = found_name
                    logs.append("Successfully recovered from RAW cache.")
                else:
                    logs.append("Fallback to RAW cache failed.")

    else:
        logs.append("Error: Could not resolve a URL to fetch.")

    return state_updates
