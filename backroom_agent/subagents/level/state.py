import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict


class LevelAgentState(TypedDict):
    url: Optional[str]
    level_name: str
    html_content: str
    force_update: bool
    level_json_generated: bool
    extracted_items_raw: List[Dict[str, Any]]
    final_items: List[Dict[str, Any]]
    extracted_entities_raw: List[Dict[str, Any]]
    final_entities: List[Dict[str, Any]]
    items_extracted: bool
    entities_extracted: bool
    logs: Annotated[List[str], operator.add]
