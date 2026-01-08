from langgraph.graph import StateGraph, START, END
from .state import LevelAgentState
from .nodes import (
    resolve_url_node,
    fetch_content_node,
    filter_items_node,
    filter_entities_node,
    update_level_json_node,
    check_completion_node
)
from .nodes_llm import (
    generate_json_node,
    extract_items_node,
    extract_entities_node
)

def completion_check(state: LevelAgentState):
    """
    Conditional logic to determine if we should update JSON or wait.
    """
    if state.get("items_extracted") and state.get("entities_extracted"):
        return "update_level_json"
    return END

# Define the Graph
workflow = StateGraph(LevelAgentState)

workflow.add_node("resolve_url", resolve_url_node)
workflow.add_node("fetch_content", fetch_content_node)
workflow.add_node("generate_json", generate_json_node)
workflow.add_node("extract_items", extract_items_node)
workflow.add_node("extract_entities", extract_entities_node)
workflow.add_node("filter_items", filter_items_node)
workflow.add_node("filter_entities", filter_entities_node)
workflow.add_node("check_completion", check_completion_node)
workflow.add_node("update_level_json", update_level_json_node)

workflow.add_edge(START, "resolve_url")
workflow.add_edge("resolve_url", "fetch_content")
workflow.add_edge("fetch_content", "generate_json")

# Fork here
workflow.add_edge("generate_json", "extract_items")
workflow.add_edge("generate_json", "extract_entities")

# Branch 1
workflow.add_edge("extract_items", "filter_items")
workflow.add_edge("filter_items", "check_completion")

# Branch 2
workflow.add_edge("extract_entities", "filter_entities")
workflow.add_edge("filter_entities", "check_completion")

# Completion Check
workflow.add_conditional_edges(
    "check_completion",
    completion_check,
    {
        "update_level_json": "update_level_json",
        END: END
    }
)

workflow.add_edge("update_level_json", END)



# Compile
level_agent = workflow.compile()
