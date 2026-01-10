import asyncio
import os
import sys
from pprint import pprint

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backroom_agent.graph import graph
from backroom_agent.protocol import EventType, GameEvent, GameState, Attributes, Vitals
from backroom_agent.constants import GraphKeys

async def main():
    print(">>> Testing INIT Event Flow...")
    
    # Mock Initial State
    game_state = GameState(
        level="Level 0",
        attributes=Attributes(STR=10, DEX=10, CON=10, INT=10, WIS=10, CHA=10),
        vitals=Vitals(hp=10, maxHp=10, sanity=100),
        inventory=[],
        time=480
    )

    # Mock Event
    event = GameEvent(type=EventType.INIT)

    # Construct Graph Input State
    # Note: State is a TypedDict, so we pass a dict
    input_state = {
        GraphKeys.EVENT: event,
        GraphKeys.USER_INPUT: "", 
        GraphKeys.SESSION_ID: "test-session-init",
        GraphKeys.CURRENT_GAME_STATE: game_state,
        GraphKeys.MESSAGES: [],
    }

    print(f">>> Invoking graph for {game_state.level}...")

    # Run the graph
    try:
        async for chunk in graph.astream(input_state, stream_mode="updates"):
            for node, updates in chunk.items():
                print(f"\n--- Node Executed: {node} ---")
                
                if "messages" in updates:
                    msgs = updates["messages"]
                    if not isinstance(msgs, list):
                        msgs = [msgs]
                    for m in msgs:
                        print(f"[Message Content]:\n{m.content}")
                
                if "suggestions" in updates:
                    print(f"[Suggestions]: {updates['suggestions']}")
                
                if "level_context" in updates:
                    print("[Router]: Level Context Loaded")

    except Exception as e:
        print(f"Error executing graph: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
