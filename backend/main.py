import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.protocol import ChatRequest, ChatResponse

app = FastAPI(title="Backroom Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development, allow all. In prod, specify frontend URL.
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes ---


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Process player input and current state, returning the DM's response and updated state.
    """
    user_input = request.player_input.lower()
    state = request.current_state

    # Mock Logic for demonstration (In real version, this calls LangGraph)
    response_text = ""
    new_vitals = state.vitals.copy()

    if "look" in user_input:
        response_text = "You look around. The yellow wallpaper seems to hum with a fluorescent buzz. Nothing has changed."
    elif "hurt" in user_input:
        response_text = "You hurt yourself in confusion!"
        new_vitals.hp -= 2
    else:
        response_text = (
            f"You tried to '{user_input}', but the Backrooms logic twists your intent."
        )

    # Prevent HP from going below 0
    new_vitals.hp = max(0, new_vitals.hp)

    # Update state
    updated_state = state.copy()
    updated_state.vitals = new_vitals

    return ChatResponse(message=response_text, sender="dm", new_state=updated_state)


@app.get("/health")
def health_check():
    return {"status": "ok"}


# --- Entry Point ---


def start():
    """Launched with `python backend/main.py`"""
    # Assuming running from the project root
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    start()
