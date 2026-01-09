import asyncio
from typing import AsyncGenerator

from langchain_core.messages import AIMessage, HumanMessage

from backroom_agent.graph import graph
from backroom_agent.protocol import (ChatRequest, GameState, LogicEvent,
                                     StreamChunkLogicEvent, StreamChunkMessage,
                                     StreamChunkState, StreamChunkSuggestions,
                                     StreamChunkType)


async def handle_message(
    request: ChatRequest, current_state: GameState
) -> AsyncGenerator[str, None]:
    # Construct the initial state for the graph execution
    # For a message event, we include the user's input as a HumanMessage
    input_state = {
        "event": request.event,
        "user_input": request.player_input,
        "session_id": request.session_id,
        "current_game_state": current_state,
        "messages": [HumanMessage(content=request.player_input)],
    }

    # Stream updates from the agent graph
    async for chunk in graph.astream(input_state, stream_mode="updates"):
        for node_name, updates in chunk.items():
            if not updates:
                continue

            # 1. Messages (from LLM or other nodes)
            if "messages" in updates:
                msgs = updates["messages"]
                if not isinstance(msgs, list):
                    msgs = [msgs]

                for msg in msgs:
                    # We typically only send back AIMessages to the frontend
                    if isinstance(msg, AIMessage) and msg.content:
                        yield StreamChunkMessage(
                            type=StreamChunkType.MESSAGE,
                            text=str(msg.content),
                            sender="dm",
                        ).model_dump_json() + "\n"

            # 2. Game State
            if "current_game_state" in updates:
                new_state = updates["current_game_state"]
                if isinstance(new_state, GameState):
                    yield StreamChunkState(
                        type=StreamChunkType.STATE, state=new_state
                    ).model_dump_json() + "\n"

            # 3. Logic Event
            if "logic_event" in updates:
                evt = updates["logic_event"]
                if isinstance(evt, LogicEvent):
                    yield StreamChunkLogicEvent(
                        type=StreamChunkType.LOGIC_EVENT, event=evt
                    ).model_dump_json() + "\n"

            # 4. Suggestions
            if "suggestions" in updates:
                suggs = updates["suggestions"]
                if isinstance(suggs, list):
                    yield StreamChunkSuggestions(
                        type=StreamChunkType.SUGGESTIONS, options=suggs
                    ).model_dump_json() + "\n"
