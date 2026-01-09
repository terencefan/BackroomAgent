import asyncio
import logging
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backroom_agent.handlers import (handle_drop_item, handle_init,
                                     handle_message, handle_use_item)
from backroom_agent.protocol import (Attributes, ChatRequest, EventType,
                                     GameState, Vitals)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Backroom Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Helper Methods ---


def get_initial_state() -> GameState:
    """Returns the default initial game state."""
    return GameState(
        level="Level 0",
        attributes=Attributes(STR=10, DEX=10, CON=10, INT=10, WIS=10, CHA=10),
        vitals=Vitals(hp=10, maxHp=10, sanity=100),
        inventory=[],
    )


async def mock_agent_generator(request: ChatRequest) -> AsyncGenerator[str, None]:
    """
    Generator that simulates the agent's thinking and response process.
    Yields NDJSON strings.
    """
    current_state = request.current_state or get_initial_state()

    # 1. Simulate processing delay
    await asyncio.sleep(0.5)

    if request.event.type == EventType.INIT:
        async for chunk in handle_init(request, current_state):
            yield chunk
    elif request.event.type == EventType.USE:
        async for chunk in handle_use_item(request, current_state):
            yield chunk
    elif request.event.type == EventType.DROP:
        async for chunk in handle_drop_item(request, current_state):
            yield chunk
    else:
        # Default/Message/Action
        async for chunk in handle_message(request, current_state):
            yield chunk


# --- Routes ---


@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest) -> StreamingResponse:
    """
    Streaming endpoint for chat interactions.
    """
    session_id = request.session_id or "NO_SESSION"
    logger.info(
        f"[{session_id}] Event: {request.event.type} | Input: {request.player_input}"
    )

    return StreamingResponse(
        mock_agent_generator(request), media_type="application/x-ndjson"
    )


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


def start() -> None:
    """Launched with `python -m backroom_agent.server`"""
    # Assuming running from the project root
    uvicorn.run("backroom_agent.server:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start()
