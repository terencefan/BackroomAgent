from langgraph.graph import StateGraph, START, END
from .state import EventAgentState
from .nodes import generate_event_node

workflow = StateGraph(EventAgentState)
workflow.add_node("generate_event", generate_event_node)
workflow.add_edge(START, "generate_event")
workflow.add_edge("generate_event", END)

event_agent = workflow.compile()
