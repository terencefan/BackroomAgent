import os
import re
import sys
import time
from urllib.parse import urlparse

import requests

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backroom_agent.tools.wiki_tools import fetch_wiki_content
from backroom_agent.utils.search import search_backrooms_wiki


def resolve_level_url(level_name):
    """
    Simulates the logic in backroom_agent/subagents/level/nodes.py
    """
    normalized_name = level_name.lower().replace(" ", "-")

    # 1. Heuristic First (Pattern Matching)
    if re.match(r"^level-\d+$", normalized_name):
        return (
            f"https://backrooms-wiki-cn.wikidot.com/{normalized_name}",
            "Heuristic (Regex)",
        )

    # 2. Search Fallback
    try:
        found_url = search_backrooms_wiki(level_name)
        if found_url:
            return found_url, "Search Found"
    except Exception:
        pass

    return (
        f"https://backrooms-wiki-cn.wikidot.com/{normalized_name}",
        "Fallback (Default)",
    )


def check_level_urls(start, end):
    print(
        f"{'Level':<10} | {'Method':<20} | {'Status':<15} | {'Content Len':<12} | {'URL'}"
    )
    print("-" * 100)

    for i in range(start, end + 1):
        level_name = f"level-{i}"

        # 1. Resolve URL
        url, method = resolve_level_url(level_name)

        # 2. Verify with Fetch Tool
        status_msg = "Unknown"
        content_len = 0

        try:
            # save_files=False to avoid cluttering disk, just verify fetch capability
            content, extracted_name = fetch_wiki_content(url, save_files=False)

            if content:
                status_msg = "✅ Success"
                content_len = len(content)
            else:
                status_msg = "❌ Failed"
        except Exception as e:
            status_msg = "💥 Error"
            # Optional: print specific error to stderr to not mess up table too much
            # sys.stderr.write(str(e) + "\n")

        print(
            f"{level_name:<10} | {method:<20} | {status_msg:<15} | {content_len:<12} | {url}"
        )
        sys.stdout.flush()

        # Random delay to be nice, even though tool has retries
        import random

        time.sleep(random.uniform(1.0, 2.0))


if __name__ == "__main__":
    check_level_urls(11, 20)
