import logging
from urllib.parse import urlparse

from ddgs import DDGS
from langsmith import traceable

logger = logging.getLogger(__name__)


@traceable(run_type="tool", name="Search Backrooms Wiki")
def search_backrooms_wiki(query_content: str) -> str | None:
    """
    Searches for a Backrooms wiki page for the given content.
    Returns the URL of the first result matching backrooms-wiki-cn.wikidot.com.

    Args:
        query_content: The term to search for (e.g., "Level 1" or "Entity 2")

    Returns:
        str: The URL if found, else None
    """
    query = f"后室 wiki {query_content}"
    target_domains = ["backrooms-wiki-cn.wikidot.com", "brcn.backroomswiki.cn"]

    logger.info(f"Searching web for: {query}")

    try:
        with DDGS() as ddgs:
            # Fetch a few more results to increase chance of hitting the specific domain
            results = ddgs.text(query, max_results=10)
            if results:
                # First pass: check for preferred domain (mirror)
                for result in results:
                    url = result.get("href")
                    if url and "brcn.backroomswiki.cn" in urlparse(url).netloc:
                        logger.info(f"Found preferred match: {url}")
                        return url

                # Second pass: check for original domain
                for result in results:
                    url = result.get("href")
                    if url and "backrooms-wiki-cn.wikidot.com" in urlparse(url).netloc:
                        logger.info(f"Found match: {url}")
                        return url
    except Exception as e:
        logger.error(f"Search error: {e}")

    return None
