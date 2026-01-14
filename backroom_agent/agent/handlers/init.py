import asyncio
from typing import AsyncGenerator, cast

from langchain_core.messages import AIMessage

from backroom_agent.agent.graph import graph
from backroom_agent.agent.state import State
from backroom_agent.protocol import (ChatRequest, GameState, StreamChunkInit,
                                     StreamChunkMessage, StreamChunkState,
                                     StreamChunkSuggestions, StreamChunkType)


async def handle_init(
    request: ChatRequest,
    current_state: GameState,
    history_messages: list | None = None,
) -> AsyncGenerator[str, None]:
    """
    Handle init event with optional message history.

    Args:
        request: Chat request
        current_state: Current game state
        history_messages: Optional message history (usually empty for init, but kept for consistency)
    """
    # Init always starts with empty messages (session is reset)
    input_state = cast(
        State,
        {
            "event": request.event,
            "user_input": request.player_input,
            "session_id": request.session_id,
            "current_game_state": current_state,
            "messages": history_messages or [],
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
