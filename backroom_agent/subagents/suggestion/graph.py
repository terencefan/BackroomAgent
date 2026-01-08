from langgraph.graph import StateGraph, START, END
from .state import SuggestionAgentState
from .nodes import generate_suggestions_node

workflow = StateGraph(SuggestionAgentState)
workflow.add_node("generate_suggestions", generate_suggestions_node)
workflow.add_edge(START, "generate_suggestions")
workflow.add_edge("generate_suggestions", END)

suggestion_agent = workflow.compile()
