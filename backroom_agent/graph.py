from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

from backroom_agent.nodes import (NODE_INIT, NODE_ITEM, NODE_LLM, NODE_MESSAGE,
                                  NODE_PROCESS_MESSAGE, NODE_ROUTER,
                                  NODE_SUGGESTION, NODE_SUMMARY, init_node,
                                  item_node, llm_node, message_node,
                                  process_message_node, route_event,
                                  router_node, suggestion_node, summary_node)
from backroom_agent.state import State


def build_graph():
    """Constructs the StateGraph for the agent."""
    workflow = StateGraph(State)

    # Add Router Node (Entry Point)
    workflow.add_node(NODE_ROUTER, router_node)

    # Add Task Nodes
    workflow.add_node(NODE_INIT, init_node)
    workflow.add_node(NODE_ITEM, item_node)
    workflow.add_node(NODE_LLM, llm_node)
    workflow.add_node(NODE_MESSAGE, message_node)
    workflow.add_node(NODE_PROCESS_MESSAGE, process_message_node)

    # Add Summary & Suggestion Nodes
    workflow.add_node(NODE_SUMMARY, summary_node)
    workflow.add_node(NODE_SUGGESTION, suggestion_node)

    # Entry Point -> Router
    workflow.add_edge(START, NODE_ROUTER)

    # Router -> Conditional Edge -> Task Nodes
    workflow.add_conditional_edges(
        NODE_ROUTER,
        route_event,
        {
            NODE_INIT: NODE_INIT,
            NODE_ITEM: NODE_ITEM,
            NODE_LLM: NODE_LLM,
            NODE_MESSAGE: NODE_MESSAGE,
        },
    )

    # Reroute all task nodes to Summary Node
    workflow.add_edge(NODE_INIT, NODE_SUMMARY)
    workflow.add_edge(NODE_ITEM, NODE_SUMMARY)
    workflow.add_edge(NODE_LLM, NODE_SUMMARY)

    # Message Node Pipeline
    workflow.add_edge(NODE_MESSAGE, NODE_PROCESS_MESSAGE)
    workflow.add_edge(NODE_PROCESS_MESSAGE, NODE_SUMMARY)

    # Summary -> Suggestion -> END
    workflow.add_edge(NODE_SUMMARY, NODE_SUGGESTION)
    workflow.add_edge(NODE_SUGGESTION, END)

    return workflow.compile()


# Validated graph instance
graph = build_graph()


def run_once(user_text: str) -> AIMessage:
    """Convenience helper for a one-turn run."""
    # Note: This helper might need update to handle event_type if used for complex testing
    # defaulting to message/llm
    result = graph.invoke(
        {"messages": [HumanMessage(content=user_text)], "event_type": "message"}
    )
    last = result["messages"][-1]
    if not isinstance(last, AIMessage):
        raise TypeError(f"Expected AIMessage, got {type(last)}")
    return last
