import operator
from typing import Annotated, List, TypedDict, Optional
from langchain_core.messages import BaseMessage

class EventAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    current_level: str
    player_status: str # Summary of health, sanity, inventory
    nearby_entities: List[str]
    event_result: Optional[str] # The generated event description
