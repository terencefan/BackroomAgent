from langgraph.graph import END, START, StateGraph
from langchain_core.messages import AIMessage, HumanMessage
from backroom_agent.state import State
from backroom_agent.agent import dm_agent

def build_graph():
    """Constructs the StateGraph for the agent."""
    workflow = StateGraph(State)
    workflow.add_node("dm_agent", dm_agent)
    workflow.add_edge(START, "dm_agent")
    workflow.add_edge("dm_agent", END)

    return workflow.compile()

# Validated graph instance
graph = build_graph()

def run_once(user_text: str) -> AIMessage:
    """Convenience helper for a one-turn run."""
    result = graph.invoke({"messages": [HumanMessage(content=user_text)]})
    last = result["messages"][-1]
    if not isinstance(last, AIMessage):
        raise TypeError(f"Expected AIMessage, got {type(last)}")
    return last
