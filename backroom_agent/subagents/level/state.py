from typing import TypedDict, List, Dict, Any, Optional

class LevelAgentState(TypedDict):
    url: Optional[str]
    level_name: str
    html_content: str
    force_update: bool
    level_json_generated: bool
    extracted_items_raw: List[Dict[str, Any]]
    final_items: List[Dict[str, Any]]
    logs: List[str]
