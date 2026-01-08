from typing import AsyncGenerator

from backroom_agent.protocol import (
    ChatRequest,
    GameState,
    StreamChunkMessage,
    StreamChunkState,
    StreamChunkSuggestions,
    StreamChunkType,
)

async def handle_use_item(request: ChatRequest, current_state: GameState) -> AsyncGenerator[str, None]:
    item_id = request.event.item_id
    # yield Message
    yield StreamChunkMessage(
        type=StreamChunkType.MESSAGE,
        text=f"Used item: {item_id}. Nothing happens.",
        sender="dm"
    ).model_dump_json() + "\n"
    
    # yield State
    yield StreamChunkState(
        type=StreamChunkType.STATE,
        state=current_state
    ).model_dump_json() + "\n"
    
    yield StreamChunkSuggestions(
        type=StreamChunkType.SUGGESTIONS,
        options=["Look around"]
    ).model_dump_json() + "\n"


async def handle_drop_item(request: ChatRequest, current_state: GameState) -> AsyncGenerator[str, None]:
    item_id = request.event.item_id
    quantity = request.event.quantity or 1
    
    # yield Message
    yield StreamChunkMessage(
        type=StreamChunkType.MESSAGE,
        text=f"Dropped {quantity} x {item_id}.",
        sender="dm"
    ).model_dump_json() + "\n"
    
    # yield State
    yield StreamChunkState(
        type=StreamChunkType.STATE,
        state=current_state
    ).model_dump_json() + "\n"
    
    yield StreamChunkSuggestions(
        type=StreamChunkType.SUGGESTIONS,
        options=["Look around"]
    ).model_dump_json() + "\n"
