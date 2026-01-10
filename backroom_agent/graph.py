from typing import cast

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

from backroom_agent.nodes import (  # Node Constants; Node Functions; Routing Functions
    NODE_DICE_NODE, NODE_DICE_RESOLVE_NODE, NODE_EVENT_NODE,
    NODE_EVENT_RESOLVE_NODE, NODE_INIT_NODE, NODE_ITEM_RESOLVE_NODE,
    NODE_ROUTER_NODE, NODE_SETTLEMENT_NODE, NODE_SUGGESTION_NODE,
    NODE_SUMMARY_NODE, dice_node, dice_resolve_node, event_node,
    event_resolve_node, init_node, item_resolve_node, route_check_dice,
    route_event, route_settle, router_node, settlement_node, suggestion_node,
    summary_node)
from backroom_agent.state import State


def build_graph():
    """Constructs the StateGraph for the agent."""
    workflow = StateGraph(State)

    # Add Router Node (Entry Point)
    workflow.add_node(NODE_ROUTER_NODE, router_node)

    # Add Task Nodes
    workflow.add_node(NODE_INIT_NODE, init_node)
    workflow.add_node(NODE_ITEM_RESOLVE_NODE, item_resolve_node)
    workflow.add_node(NODE_EVENT_NODE, event_node)
    workflow.add_node(NODE_DICE_NODE, dice_node)
    workflow.add_node(NODE_DICE_RESOLVE_NODE, dice_resolve_node)
    workflow.add_node(NODE_EVENT_RESOLVE_NODE, event_resolve_node)

    # Add Convergence, Summary & Suggestion Nodes
    workflow.add_node(NODE_SETTLEMENT_NODE, settlement_node)
    workflow.add_node(NODE_SUMMARY_NODE, summary_node)
    workflow.add_node(NODE_SUGGESTION_NODE, suggestion_node)

    # Entry Point -> Router
    workflow.add_edge(START, NODE_ROUTER_NODE)

    # Router -> Conditional Edge -> Task Nodes
    # The return values of route_event match these keys
    # Note: router still returns ITEM_NODE constant if check is based on string.
    # We must ensure router.py returns consistent keys or we map them here.
    # Assuming router returns standard keys which map to these Node IDs.
    workflow.add_conditional_edges(
        NODE_ROUTER_NODE,
        route_event,
        {
            NODE_INIT_NODE: NODE_INIT_NODE,
            "item_node": NODE_ITEM_RESOLVE_NODE, # Map old key to new node
            NODE_EVENT_NODE: NODE_EVENT_NODE,
            END: END,
        },
    )

    # Reroute standard task nodes to Settlement Node
    workflow.add_edge(NODE_INIT_NODE, NODE_SUMMARY_NODE)
    workflow.add_edge(NODE_ITEM_RESOLVE_NODE, NODE_SETTLEMENT_NODE)

    # The Generation Loop:
    # 1. Event (LLM Generate + Process)
    # 2. Check Dice?
    # 3. Yes -> Dice -> Dice Resolve -> Event (Loop)
    # 4. No -> Event Resolve -> Settlement

    workflow.add_conditional_edges(
        NODE_EVENT_NODE,
        route_check_dice,
        {
            NODE_DICE_NODE: NODE_DICE_NODE,
            NODE_EVENT_RESOLVE_NODE: NODE_EVENT_RESOLVE_NODE,
        },
    )

    # Dice Result -> Dice Resolve -> Event Loop
    workflow.add_edge(NODE_DICE_NODE, NODE_DICE_RESOLVE_NODE)
    workflow.add_edge(NODE_DICE_RESOLVE_NODE, NODE_EVENT_NODE)

    # Event Resolve -> Settlement
    workflow.add_conditional_edges(
        NODE_EVENT_RESOLVE_NODE,
        route_settle,
        {NODE_SETTLEMENT_NODE: NODE_SETTLEMENT_NODE},
    )

    # Settlement -> Summary -> Suggestion -> END
    workflow.add_edge(NODE_SETTLEMENT_NODE, NODE_SUMMARY_NODE)
    workflow.add_edge(NODE_SUMMARY_NODE, NODE_SUGGESTION_NODE)
    workflow.add_edge(NODE_SUGGESTION_NODE, END)

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
