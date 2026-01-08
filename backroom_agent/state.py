from typing import Annotated, TypedDict, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class State(TypedDict):
    """The shared state of the Backroom Agent graph."""
    messages: Annotated[List[BaseMessage], add_messages]
