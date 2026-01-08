from langgraph.graph import StateGraph, START, END
from .state import LevelAgentState
from .nodes import (
    resolve_url_node,
    fetch_content_node,
    generate_json_node,
    extract_items_node,
    filter_items_node,
    update_level_json_node
)

# Define the Graph
workflow = StateGraph(LevelAgentState)

workflow.add_node("resolve_url", resolve_url_node)
workflow.add_node("fetch_content", fetch_content_node)
workflow.add_node("generate_json", generate_json_node)
workflow.add_node("extract_items", extract_items_node)
workflow.add_node("filter_items", filter_items_node)
workflow.add_node("update_level_json", update_level_json_node)

workflow.add_edge(START, "resolve_url")
workflow.add_edge("resolve_url", "fetch_content")
workflow.add_edge("fetch_content", "generate_json")
workflow.add_edge("generate_json", "extract_items")
workflow.add_edge("extract_items", "filter_items")
workflow.add_edge("filter_items", "update_level_json")
workflow.add_edge("update_level_json", END)

# Compile
level_agent = workflow.compile()
