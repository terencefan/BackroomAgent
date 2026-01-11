import asyncio
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backroom_agent.agent.handlers.message import handle_message
from backroom_agent.protocol import (Attributes, ChatRequest, EventType,
                                     GameEvent, GameState, Vitals)
from backroom_agent.utils.logger import logger


async def test_streaming_dice():
    print("--- Starting Streaming Test ---")

    # 1. Setup Request
    # We want to trigger a dice roll.
    # Usually "Search the room" triggers a LogicEvent -> DiceRoll.
    state = GameState(
        level="Level 0",
        attributes=Attributes(STR=10, DEX=10, CON=10, INT=10, WIS=10, CHA=10),
        vitals=Vitals(hp=10, maxHp=10, sanity=100),
        inventory=[],
    )

    request = ChatRequest(
        event=GameEvent(type=EventType.MESSAGE),
        player_input="Search the room carefully for hidden items.",  # High probability of dice roll
        session_id="test_session",
        current_state=state,
    )

    # 2. Run Handler
    print("Invoking handle_message...")
    async for chunk in handle_message(request, state):
        print(f"CHUNK: {chunk.strip()}")
        if "dice_roll" in chunk:
            print(">>> DICE ROLL DETECTED <<<")
        if "settlement" in chunk:
            print(">>> SETTLEMENT DETECTED <<<")

    print("--- Test Complete ---")


if __name__ == "__main__":
    asyncio.run(test_streaming_dice())
