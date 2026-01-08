import operator
from typing import Annotated, List, TypedDict, Optional
from langchain_core.messages import BaseMessage

class SuggestionAgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    current_context: str
    valid_actions: List[str]
    suggestions: Optional[List[str]]
