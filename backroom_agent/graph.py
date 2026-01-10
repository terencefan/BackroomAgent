from typing import cast

from langchain_core.messages import AIMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

from backroom_agent.nodes import (  # Node Constants; Node Functions; Routing Functions
    NODE_DICE_NODE, NODE_INIT_NODE, NODE_ITEM_NODE, NODE_MESSAGE_NODE,
    NODE_PROCESS_MESSAGE_NODE, NODE_ROUTER_NODE, NODE_SETTLE_NODE,
    NODE_SUGGESTION_NODE, NODE_SUMMARY_NODE, dice_node, init_node, item_node,
    message_node, process_message_node, route_check_dice, route_event,
    route_settle, router_node, settle_node, suggestion_node, summary_node)
from backroom_agent.state import State


def build_graph():
    """Constructs the StateGraph for the agent."""
    workflow = StateGraph(State)

    # Add Router Node (Entry Point)
    workflow.add_node(NODE_ROUTER_NODE, router_node)

    # Add Task Nodes
    workflow.add_node(NODE_INIT_NODE, init_node)
    workflow.add_node(NODE_ITEM_NODE, item_node)
    workflow.add_node(NODE_MESSAGE_NODE, message_node)
    workflow.add_node(NODE_PROCESS_MESSAGE_NODE, process_message_node)
    workflow.add_node(NODE_DICE_NODE, dice_node)
    workflow.add_node(NODE_SETTLE_NODE, settle_node)

    # Add Summary (Update) & Suggestion Nodes
    workflow.add_node(NODE_SUMMARY_NODE, summary_node)
    workflow.add_node(NODE_SUGGESTION_NODE, suggestion_node)

    # Entry Point -> Router
    workflow.add_edge(START, NODE_ROUTER_NODE)

    # Router -> Conditional Edge -> Task Nodes
    # The return values of route_event match these keys
    workflow.add_conditional_edges(
        NODE_ROUTER_NODE,
        route_event,
        {
            NODE_INIT_NODE: NODE_INIT_NODE,
            NODE_ITEM_NODE: NODE_ITEM_NODE,
            NODE_MESSAGE_NODE: NODE_MESSAGE_NODE,
            END: END,
        },
    )

    # Reroute standard task nodes to Update (Summary) Node
    workflow.add_edge(NODE_INIT_NODE, NODE_SUMMARY_NODE)
    workflow.add_edge(NODE_ITEM_NODE, NODE_SUMMARY_NODE)

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

    workflow.add_edge(NODE_MESSAGE_NODE, NODE_PROCESS_MESSAGE_NODE)

    workflow.add_conditional_edges(
        NODE_PROCESS_MESSAGE_NODE,
        route_check_dice,
        {NODE_DICE_NODE: NODE_DICE_NODE, NODE_SETTLE_NODE: NODE_SETTLE_NODE},
    )

    # Dice Result -> Generate Node (LLM continues using dice feedback message)
    workflow.add_edge(NODE_DICE_NODE, NODE_MESSAGE_NODE)

    # Settle -> (Check next_step) -> Summary OR Generate
    workflow.add_conditional_edges(
        NODE_SETTLE_NODE,
        route_settle,
        {NODE_SUMMARY_NODE: NODE_SUMMARY_NODE, NODE_MESSAGE_NODE: NODE_MESSAGE_NODE},
    )

    # Update -> Suggest -> END
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
