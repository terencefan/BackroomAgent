from typing import Callable, List, Optional, Tuple

from backroom_agent.utils.node_annotation import annotate_node

from ..state import LevelAgentState


def _filter_candidates(
    candidates: List[dict],
    html_content: str,
    logs: List[str],
    category_label: str,
) -> List[dict]:
    """
    Abstracted logic for filtering lists of candidates.
    1. Hallucination Check (name presence).
    """
    final_list = []
    logs.append(f"Filtering {category_label}...")
    total = len(candidates)

    for i, item in enumerate(candidates):
        name = item.get("name")
        logs.append(f"Processing {category_label} {i+1}/{total}: {name}")

        # 1. Hallucination Check
        if not isinstance(name, str) or name not in html_content:
            logs.append(f"Filtered (Hallucination): '{name}' not found in source text.")
            continue

        final_list.append(item)
        logs.append(f"Accepted: {name}")

    return final_list


@annotate_node("normal")
def filter_items_node(state: LevelAgentState):
    """
    Filters extracted items based on:
    1. Hallucination check.
    """
    logs = state.get("logs", [])
    raw_items = state.get("extracted_items_raw", [])
    html_content = state.get("html_content", "")

    final_items = _filter_candidates(
        candidates=raw_items,
        html_content=html_content,
        logs=logs,
        category_label="items",
    )

    return {"final_items": final_items, "logs": logs, "items_extracted": True}


@annotate_node("normal")
def filter_entities_node(state: LevelAgentState):
    """
    Filters extracted entities based on:
    1. Hallucination check.
    """
    logs = state.get("logs", [])
    raw_entities = state.get("extracted_entities_raw", [])
    html_content = state.get("html_content", "")

    final_entities = _filter_candidates(
        candidates=raw_entities,
        html_content=html_content,
        logs=logs,
        category_label="entities",
    )

    return {"final_entities": final_entities, "logs": logs, "entities_extracted": True}
