from langgraph.graph import END, START, StateGraph

from .nodes import generate_event_node
from .state import EventAgentState

workflow = StateGraph(EventAgentState)
workflow.add_node("generate_event", generate_event_node)
workflow.add_edge(START, "generate_event")
workflow.add_edge("generate_event", END)

event_agent = workflow.compile()
