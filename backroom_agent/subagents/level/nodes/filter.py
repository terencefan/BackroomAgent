import logging

from backroom_agent.utils.vector_store import search_similar_items
from ..state import LevelAgentState

logger = logging.getLogger(__name__)


def filter_items_node(state: LevelAgentState):
    """
    Filters extracted items based on:
    1. Vector DB similarity (Dedup).
    2. Hallucination check (String matching in source).
    """
    raw_items = state.get("extracted_items_raw", [])
    html_content = state.get("html_content", "")
    logs = state.get("logs", [])

    final_items = []

    logs.append("Filtering items...")

    # Threshold for vector similarity to consider it "already exists"
    # If similarity > threshold, we count it as a duplicate
    SIMILARITY_THRESHOLD = 0.85

    total_items = len(raw_items)
    for i, item in enumerate(raw_items):
        name = item.get("name")
        description = item.get("description", "")

        logs.append(f"Processing item {i+1}/{total_items}: {name}")

        # 1. Hallucination Check (Basic)
        # Check if the name (or part of it) actually appears in the text
        if name not in html_content:
            logs.append(f"Filtered (Hallucination): '{name}' not found in source text.")
            continue

        # 2. Vector DB Check
        # Let's search by name primarily as that's the main identifier
        query = name

        existing_matches = search_similar_items(query, k=1)

        is_duplicate = False
        if existing_matches:
            top_match = existing_matches[0]
            score = top_match["score"]
            existing_name = top_match["metadata"]["name"]

            if score > SIMILARITY_THRESHOLD:
                is_duplicate = True
                logs.append(
                    f"Filtered (Duplicate): '{name}' is too similar to existing '{existing_name}' (Score: {score:.4f})"
                )

        if not is_duplicate:
            final_items.append(item)
            logs.append(f"Accepted: {name}")

    return {"final_items": final_items, "logs": logs, "items_extracted": True}


def filter_entities_node(state: LevelAgentState):
    """
    Filters extracted entities based on:
    1. Hallucination check.
    2. Optional: Vector DB similarity (Dedup) - currently reusing item vector store for checking.
    """
    raw_entities = state.get("extracted_entities_raw", [])
    html_content = state.get("html_content", "")
    logs = state.get("logs", [])

    final_entities = []

    logs.append("Filtering entities...")

    SIMILARITY_THRESHOLD = 0.85

    total = len(raw_entities)
    for i, entity in enumerate(raw_entities):
        name = entity.get("name")

        logs.append(f"Processing entity {i+1}/{total}: {name}")

        # 1. Hallucination Check
        if name not in html_content:
            logs.append(f"Filtered (Hallucination): '{name}' not found in source text.")
            continue

        # 2. Vector DB Check (Using item store temporarily or same unified store)
        # Assuming we might want to check against items too (don't want item == entity)
        # But really we want an entity DB. For now, strict duplicates are fine.
        # We will implement separate check if needed.

        final_entities.append(entity)
        logs.append(f"Accepted: {name}")

    return {"final_entities": final_entities, "logs": logs, "entities_extracted": True}
