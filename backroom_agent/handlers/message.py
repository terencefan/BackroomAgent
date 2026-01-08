import asyncio
from typing import AsyncGenerator

from backroom_agent.protocol import (
    ChatRequest,
    GameState,
    StreamChunkMessage,
    StreamChunkState,
    StreamChunkSuggestions,
    StreamChunkType,
)

async def handle_message(request: ChatRequest, current_state: GameState) -> AsyncGenerator[str, None]:
    user_input = request.player_input
    
    # Logic: Basic echo or keyword response
    response_text = f"You said: '{user_input}'. The walls seem to absorb your words."
    if "look" in user_input.lower():
        response_text = "You see endless yellow wallpaper, damp and mono-yellow."
    
    # yield Message
    yield StreamChunkMessage(
        type=StreamChunkType.MESSAGE,
        text=response_text,
        sender="dm"
    ).model_dump_json() + "\n"

    await asyncio.sleep(0.5)

    # Update State (Mock: reduce sanity slightly on 'listen')
    # Use model_copy() for Pydantic v2, or copy() for v1.
    try:
        new_state = current_state.model_copy(deep=True)
    except AttributeError:
        new_state = current_state.copy(deep=True) # v1

    if "listen" in user_input.lower():
        new_state.vitals.sanity = max(0, new_state.vitals.sanity - 5)
        yield StreamChunkMessage(
            type=StreamChunkType.MESSAGE,
            text="The buzzing noise gnaws at your mind. -5 Sanity.",
            sender="system"
        ).model_dump_json() + "\n"

    # yield State
    yield StreamChunkState(
        type=StreamChunkType.STATE,
        state=new_state
    ).model_dump_json() + "\n"

    await asyncio.sleep(0.2)

    # yield Suggestions
    yield StreamChunkSuggestions(
        type=StreamChunkType.SUGGESTIONS,
        options=["Look around", "Walk forward", "Listen carefully"]
    ).model_dump_json() + "\n"
