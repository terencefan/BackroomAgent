from typing import cast

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

from backroom_agent.nodes import (
    # Node Constants
    NODE_DICE,
    NODE_GENERATE,
    NODE_INIT,
    NODE_INVENTORY,
    NODE_PROCESS,
    NODE_ROUTER,
    NODE_SETTLE,
    NODE_SUGGEST,
    NODE_SUMMARY,
    # Node Functions
    dice_node,
    init_node,
    item_node,
    message_node,
    process_message_node,
    router_node,
    settle_node,
    suggestion_node,
    summary_node,
    # Routing Functions
    route_check_dice,
    route_event,
    route_settle,
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
    workflow.add_node(NODE_SETTLE, settle_node)

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
    # 4. If Dice needed: Dice Node -> Settle Node
    # 5. If No Dice: -> Settle Node (Wait, Process -> Settle directly? Or Summary?)
    #    Actually current flow:
    #    Generate -> Process (Check Dice?) -> [Yes -> Dice] OR [No -> Summary?]
    #    Revised FLow:
    #    Generate -> Process
    #       -> (LogicEvent?) -> Yes -> Dice -> Settle
    #       -> No -> Settle (To confirm narrative?) OR Summary?
    #    The Request: "dice 和 process 后面需要加一个结算节点"
    #    So: Process -> Settle (if no dice) AND Dice -> Settle.

    workflow.add_edge(NODE_GENERATE, NODE_PROCESS)

    workflow.add_conditional_edges(
        NODE_PROCESS,
        route_check_dice,
        {NODE_DICE: NODE_DICE, NODE_SETTLE: NODE_SETTLE},
    )

    # Dice Result -> Generate Node (LLM continues using dice feedback message)
    workflow.add_edge(NODE_DICE, NODE_GENERATE)

    # Settle -> (Check next_step) -> Summary OR Generate
    workflow.add_conditional_edges(
        NODE_SETTLE,
        route_settle,
        {NODE_SUMMARY: NODE_SUMMARY, NODE_GENERATE: NODE_GENERATE},
    )

    # Update -> Suggest -> END
    workflow.add_edge(NODE_SUMMARY, NODE_SUGGEST)
    workflow.add_edge(NODE_SUGGEST, END)

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
