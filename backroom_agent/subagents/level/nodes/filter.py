import logging
from typing import Callable, List, Optional, Tuple

from backroom_agent.utils.vector_store import search_similar_items

from ..state import LevelAgentState

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.85


def _check_similarity(name: str) -> Tuple[bool, Optional[str]]:
    """
    Checks for similarity against existing items in the Vector Store.
    Returns: (is_duplicate, reason_message)
    """
    matches = search_similar_items(name, k=1)
    if matches:
        top_match = matches[0]
        score = top_match["score"]
        existing_name = top_match["metadata"]["name"]

        if score > SIMILARITY_THRESHOLD:
            return (
                True,
                f"Filtered (Duplicate): '{name}' is too similar to existing '{existing_name}' (Score: {score:.4f})",
            )

    return False, None


def _filter_candidates(
    candidates: List[dict],
    html_content: str,
    logs: List[str],
    category_label: str,
    check_fn: Optional[Callable[[str], Tuple[bool, Optional[str]]]] = None,
) -> List[dict]:
    """
    Abstracted logic for filtering lists of candidates.
    1. Hallucination Check (name presence).
    2. Optional Custom Check (e.g., Vector Similarity).
    """
    final_list = []
    logs.append(f"Filtering {category_label}...")
    total = len(candidates)

    for i, item in enumerate(candidates):
        name = item.get("name")
        logs.append(f"Processing {category_label} {i+1}/{total}: {name}")

        # 1. Hallucination Check
        if name not in html_content:
            logs.append(f"Filtered (Hallucination): '{name}' not found in source text.")
            continue

        # 2. Custom/Similarity Check
        if check_fn:
            is_dup, reason = check_fn(name)
            if is_dup:
                logs.append(reason)
                continue

        final_list.append(item)
        logs.append(f"Accepted: {name}")

    return final_list


def filter_items_node(state: LevelAgentState):
    """
    Filters extracted items based on:
    1. Hallucination check.
    2. Vector DB similarity (Dedup).
    """
    logs = state.get("logs", [])
    raw_items = state.get("extracted_items_raw", [])
    html_content = state.get("html_content", "")

    final_items = _filter_candidates(
        candidates=raw_items,
        html_content=html_content,
        logs=logs,
        category_label="items",
        check_fn=_check_similarity,
    )

    return {"final_items": final_items, "logs": logs, "items_extracted": True}


def filter_entities_node(state: LevelAgentState):
    """
    Filters extracted entities based on:
    1. Hallucination check.
    2. (Placeholder) Vector DB similarity.
    """
    logs = state.get("logs", [])
    raw_entities = state.get("extracted_entities_raw", [])
    html_content = state.get("html_content", "")

    final_entities = _filter_candidates(
        candidates=raw_entities,
        html_content=html_content,
        logs=logs,
        category_label="entities",
        check_fn=None,  # No strict similarity check for entities currently
    )

    return {"final_entities": final_entities, "logs": logs, "entities_extracted": True}
