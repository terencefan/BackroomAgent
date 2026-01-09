from langgraph.graph import END, START, StateGraph

from backroom_agent.state import State

from .nodes import generate_suggestions_node

workflow = StateGraph(State)
workflow.add_node("generate_suggestions", generate_suggestions_node)
workflow.add_edge(START, "generate_suggestions")
workflow.add_edge("generate_suggestions", END)

suggestion_agent = workflow.compile()
