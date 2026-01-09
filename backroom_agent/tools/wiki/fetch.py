import os
import random
import time
from urllib.parse import urlparse

import requests

from backroom_agent.tools.wiki.constants import REQUEST_HEADERS
from backroom_agent.utils.common import get_project_root


def get_level_name_from_url(url: str) -> str:
    """Extracts the level name from the URL."""
    path = urlparse(url).path
    return path.strip("/").split("/")[-1]


def fetch_url_content(url: str, retries: int = 4) -> str | None:
    """
    Fetches raw content from a URL with retries and browser headers.
    """
    try:
        for attempt in range(retries):
            try:
                response = requests.get(url, headers=REQUEST_HEADERS, timeout=30)
                if response.status_code == 200:
                    return response.text
                elif response.status_code == 404:
                    print(f"URL not found: {url}")
                    return None
            except requests.RequestException as e:
                print(f"Attempt {attempt+1} failed for {url}: {e}")
                if attempt == retries - 1:
                    raise

                wait_time = (2**attempt) + random.uniform(0.5, 1.5)
                time.sleep(wait_time)

        return None
    except requests.RequestException as e:
        print(f"Error fetching URL: {str(e)}")
        return None
