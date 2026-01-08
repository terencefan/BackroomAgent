# Project Architecture & Guidelines

This project is a text-adventure game system composed of three distinct parts:
1.  **Agent Core** (`backroom_agent/`): Logic for the Game Master using LangGraph.
2.  **Backend** (`backend/`): FastAPI wrapper providing HTTP access to the agent.
3.  **Frontend** (`frontend/`): React + Vite terminal-style UI.

## Cross-Stack Data Protocol
The communication contract is strictly defined in `PROTOCOL.md`.
- **Python**: Models are in `backend/protocol.py` (Pydantic).
- **TypeScript**: Interfaces are in `frontend/src/types.ts`.
- **Rule**: Any change to the game state structure (e.g., adding a new stat) **MUST** be applied synchronously to `PROTOCOL.md`, `backend/protocol.py`, and `frontend/src/types.ts`.

## Agent Development (`backroom_agent/`)
- **Structure**:
    - `agent.py`: LLM node definition, system prompt loading.
    - `graph.py`: StateGraph construction and compilation.
    - `state.py`: TypedDict definition for graph state.
- **Prompts**: DO NOT hardcode prompts in Python.
    - Store prompts in `prompts/<role>_agent.md`.
    - Load dynamically using `_load_system_prompt()` pattern (see `backroom_agent/agent.py`).
- **Configuration**:
    - Access config via `backroom_agent.constants`.
    - NEVER use `os.getenv` directly in business logic (except in `constants.py`).

## Backend Development (`backend/`)
- **Entry Point**: `python backend/main.py` (Starts Uvicorn on port 8000).
- **Role**: Thin wrapper. It parses the frontend JSON, invokes the LangGraph agent, and returns the narrative + state diff.

## Frontend Development (`frontend/`)
- **State Management**: `App.tsx` is the source of truth for `attributes`, `vitals`, and `inventory`.
- **Network**: All API calls go to `http://localhost:8000/api/chat`.
- **Typing**: Always import types from `./types.ts`. Avoid `any`.
    - Example: `const data: ChatResponse = await response.json();`

## Workflows
- **Test Agent Logic**: `python scripts/test_agent.py` (Runs a single turn without starting the server).
- **Build Frontend**: `cd frontend && npm run build` (Checks TS types and builds assets).
