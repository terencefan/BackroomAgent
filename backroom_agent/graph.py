from typing import cast

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

from backroom_agent.nodes import (  # Node Constants; Node Functions; Routing Functions
    NODE_DICE_NODE, NODE_EVENT_NODE,
    NODE_RESOLVE_NODE, NODE_ROUTER_NODE, NODE_SUMMARY_NODE,
    dice_node, event_node,
    resolve_node, route_check_dice, route_event, router_node,
    summary_node)
from backroom_agent.state import State


def build_graph():
    """Constructs the StateGraph for the agent."""
    workflow = StateGraph(State)

    # Add Router Node (Entry Point)
    workflow.add_node(NODE_ROUTER_NODE, router_node)

    # Add Task Nodes
    # workflow.add_node(NODE_INIT_NODE, init_node) # DEPRECATED
    # workflow.add_node(NODE_ITEM_RESOLVE_NODE, item_resolve_node) # DEPRECATED
    workflow.add_node(NODE_EVENT_NODE, event_node)
    workflow.add_node(NODE_DICE_NODE, dice_node)
    workflow.add_node(NODE_RESOLVE_NODE, resolve_node)

    # Add Convergence, Summary Node (Suggestion Node Removed)
    workflow.add_node(NODE_SUMMARY_NODE, summary_node)

    # Entry Point -> Router
    workflow.add_edge(START, NODE_ROUTER_NODE)

    # Router -> Conditional Edge -> Task Nodes
    workflow.add_conditional_edges(
        NODE_ROUTER_NODE,
        route_event,
        {
            # NODE_INIT_NODE: NODE_INIT_NODE, # Removed
            # "item_node": NODE_ITEM_RESOLVE_NODE,  # Removed
            NODE_EVENT_NODE: NODE_EVENT_NODE,
            END: END,
        },
    )

    # Reroute standard task nodes
    # workflow.add_edge(NODE_INIT_NODE, NODE_SUMMARY_NODE) # Removed
    # workflow.add_edge(NODE_ITEM_RESOLVE_NODE, NODE_RESOLVE_NODE) # Removed

    # The Generation Loop:
    # 1. Event (LLM Generate + Process)
    # 2. Check Dice?
    # 3. Yes -> Dice (Roll + Update) -> Event (Loop)
    # 4. No -> Resolve -> Summary

    workflow.add_conditional_edges(
        NODE_EVENT_NODE,
        route_check_dice,
        {
            NODE_DICE_NODE: NODE_DICE_NODE,
            NODE_RESOLVE_NODE: NODE_RESOLVE_NODE,
        },
    )

    # Dice Result -> Event Loop (to narrate outcome)
    workflow.add_edge(NODE_DICE_NODE, NODE_EVENT_NODE)

    # Resolve -> Summary -> END
    workflow.add_edge(NODE_RESOLVE_NODE, NODE_SUMMARY_NODE)
    workflow.add_edge(NODE_SUMMARY_NODE, END)
    # workflow.add_edge(NODE_SUGGESTION_NODE, END) # REMOVED

    return workflow.compile()


# Validated graph instance
graph = build_graph()


async def run_once(user_text: str) -> AIMessage:
    """Convenience helper for a one-turn run."""
    # Note: This helper might need update to handle event_type if used for complex testing
    # defaulting to message/llm
    input_state = cast(
        State, {"messages": [HumanMessage(content=user_text)], "event_type": "message"}
    )
    result = await graph.ainvoke(input_state)
    last = result["messages"][-1]
    if not isinstance(last, AIMessage):
        raise TypeError(f"Expected AIMessage, got {type(last)}")
    return last
