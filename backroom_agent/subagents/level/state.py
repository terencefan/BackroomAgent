import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict


class LevelAgentState(TypedDict):
    # --- Input / Config ---
    force_update: bool

    # --- Shared / Accumulators ---
    logs: Annotated[List[str], operator.add]

    # --- Node: fetch_content ---
    url: Optional[str]
    level_name: str
    html_content: str
    extracted_links: List[Dict[str, str]]

    # --- Node: generate_json ---
    level_json_generated: bool

    # --- Node: extract_items ---
    extracted_items_raw: List[Dict[str, Any]]

    # --- Node: filter_items ---
    final_items: List[Dict[str, Any]]
    items_extracted: bool

    # --- Node: extract_entities ---
    extracted_entities_raw: List[Dict[str, Any]]

    # --- Node: filter_entities ---
    final_entities: List[Dict[str, Any]]
    entities_extracted: bool
