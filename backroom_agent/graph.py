from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

from backroom_agent.nodes import (
    NODE_DICE,
    NODE_GENERATE,
    NODE_INIT,
    NODE_INVENTORY,
    NODE_PROCESS,
    NODE_ROUTER,
    NODE_SUGGEST,
    NODE_SUMMARY,
    dice_node,
    init_node,
    item_node,
    message_node,
    process_message_node,
    route_check_dice,
    route_event,
    router_node,
    suggestion_node,
    summary_node,
)
from backroom_agent.state import State


def build_graph():
    """Constructs the StateGraph for the agent."""
    workflow = StateGraph(State)

    # Add Router Node (Entry Point)
    workflow.add_node(NODE_ROUTER, router_node)

    # Add Task Nodes
    workflow.add_node(NODE_INIT, init_node)
    workflow.add_node(NODE_INVENTORY, item_node)
    workflow.add_node(NODE_GENERATE, message_node)
    workflow.add_node(NODE_PROCESS, process_message_node)
    workflow.add_node(NODE_DICE, dice_node)

    # Add Summary (Update) & Suggestion Nodes
    workflow.add_node(NODE_SUMMARY, summary_node)
    workflow.add_node(NODE_SUGGEST, suggestion_node)

    # Entry Point -> Router
    workflow.add_edge(START, NODE_ROUTER)

    # Router -> Conditional Edge -> Task Nodes
    # The return values of route_event match these keys
    workflow.add_conditional_edges(
        NODE_ROUTER,
        route_event,
        {
            NODE_INIT: NODE_INIT,
            NODE_INVENTORY: NODE_INVENTORY,
            NODE_GENERATE: NODE_GENERATE,
            END: END,
        },
    )

    # Reroute standard task nodes to Update (Summary) Node
    workflow.add_edge(NODE_INIT, NODE_SUMMARY)
    workflow.add_edge(NODE_INVENTORY, NODE_SUMMARY)

    # The Generation Loop:
    # 1. Generate (LLM creates text/data)
    # 2. Process (Parser extracts events/logic)
    # 3. Dice Check (If dice event needed, roll it)
    # 4. If Dice needed: Dice Node -> Loop back to Generate (to narrate result)
    # 5. If No Dice: -> Update Node
    
    workflow.add_edge(NODE_GENERATE, NODE_PROCESS)
    
    workflow.add_conditional_edges(
        NODE_PROCESS,
        route_check_dice,
        {
            NODE_DICE: NODE_DICE,
            NODE_SUMMARY: NODE_SUMMARY
        }
    )
    
    # Send Dice Result BACK to Generate Node (LLM Inference) to narrate outcome
    workflow.add_edge(NODE_DICE, NODE_GENERATE) 
    # NOTE: This creates a loop. Dice Node MUST clear GraphKeys.LOGIC_EVENT to break it.
    
    # Update -> Suggest -> END
    workflow.add_edge(NODE_SUMMARY, NODE_SUGGEST)
    workflow.add_edge(NODE_SUGGEST, END)

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
