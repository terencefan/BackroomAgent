import asyncio
from typing import AsyncGenerator, cast

from langchain_core.messages import AIMessage

from backroom_agent.graph import graph
from backroom_agent.protocol import (ChatRequest, GameState, StreamChunkInit,
                                     StreamChunkMessage, StreamChunkState,
                                     StreamChunkSuggestions, StreamChunkType)
from backroom_agent.state import State


async def handle_init(
    request: ChatRequest, current_state: GameState
) -> AsyncGenerator[str, None]:
    input_state = cast(
        State,
        {
            "event": request.event,
            "user_input": request.player_input,
            "session_id": request.session_id,
            "current_game_state": current_state,
            "messages": [],
        },
    )

    async for chunk in graph.astream(input_state, stream_mode="updates"):
        for _, updates in chunk.items():
            if not updates:
                continue

            # 1. Messages -> INIT Type
            if "messages" in updates:
                msgs = updates["messages"]
                if not isinstance(msgs, list):
                    msgs = [msgs]

                for msg in msgs:
                    if isinstance(msg, AIMessage) and msg.content:
                        # Use StreamChunkInit for initialization messages
                        yield StreamChunkInit(
                            type=StreamChunkType.INIT,
                            text=str(msg.content),
                        ).model_dump_json() + "\n"

            # 2. Game State
            if "current_game_state" in updates:
                new_state = updates["current_game_state"]
                # Only yield if it's actually a GameState object (just safety)
                if isinstance(new_state, GameState):
                    yield StreamChunkState(
                        type=StreamChunkType.STATE, state=new_state
                    ).model_dump_json() + "\n"

            # 3. Suggestions
            if "suggestions" in updates:
                suggs = updates["suggestions"]
                if isinstance(suggs, list):
                    yield StreamChunkSuggestions(
                        type=StreamChunkType.SUGGESTIONS, options=suggs
                    ).model_dump_json() + "\n"
