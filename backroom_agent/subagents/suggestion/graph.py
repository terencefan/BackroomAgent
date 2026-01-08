from langgraph.graph import END, START, StateGraph

from .nodes import generate_suggestions_node
from .state import SuggestionAgentState

workflow = StateGraph(SuggestionAgentState)
workflow.add_node("generate_suggestions", generate_suggestions_node)
workflow.add_edge(START, "generate_suggestions")
workflow.add_edge("generate_suggestions", END)

suggestion_agent = workflow.compile()
