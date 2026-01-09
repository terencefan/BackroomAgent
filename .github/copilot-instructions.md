# BackroomAgent Guidelines

## System Architecture
Text-adventure game system composed of three main services:
1.  **Agent Core**: Python monolith (`backroom_agent/`) exposing a FastAPI server (`server.py`) and orchestrating LangGraph logic (`graph.py`).
2.  **Frontend**: React + Vite application (`frontend/`) simulating a retro terminal interface.
3.  **Data Pipeline**: Go service (`go_agent/`) for high-concurrency scraping of Wiki data into structured JSON level data.

## Critical Data Protocols
**Strict type synchronization** is enforced across the stack. The source of truth is `PROTOCOL.md`.
Any change to Game State, Events, or Item schemas must be reflected simultaneously in:
- `PROTOCOL.md` (Definition)
- `backroom_agent/protocol.py` (Python Pydantic Models)
- `frontend/src/types.ts` (TypeScript Interfaces)
- `go_agent/agent/model/state.go` (Go Structs for generation)

## Development Workflows
- **Backend Server**: `python -m backroom_agent.server` (runs on port 8000).
- **Frontend**: `cd frontend && npm run dev` (runs on port 5173). Build: `npm run build`.
- **Agent Testing**: Use `scripts/` to run agents in isolation without the server.
    - `python scripts/run_agent.py`: Interactive DM loop.
    - `python scripts/run_level_agent.py "Level 1"`: Generate level data.
- **Data Scraping**: `cd go_agent && go run main.go -name "Level X"` (or `-batch`).
- **Graph Viz**: `make graph` generates architecture diagrams in `tmp/`.

## Key Code Patterns
- **Subagents (`backroom_agent/subagents/`)**: Functional units (Level, Event, Suggestion). Each MUST define:
    - `state.py`: TypedDict state definition.
    - `graph.py`: StateGraph construction.
    - `nodes.py` OR `nodes/` module: Logic implementation.
- **Vector Store**: Custom `numpy`/`pickle` implementation in `backroom_agent/utils/vector_store.py`. Avoid external vector DBs (Chroma/Pinecone).
- **Configuration**: All config/env access via `backroom_agent.constants`. Avoid direct `os.getenv` in logic.
- **Prompts**: Store in `prompts/*.prompt`. Never hardcode. Use `_load_system_prompt`.
- **Refs**: Item/Entity references in `analysis.py` are now lists of strings (Ids/Names), not full objects.

## Tech Stack Details
- **Python**: 3.12+, LangGraph, FastAPI, Pydantic.
- **Frontend**: React, TypeScript, TailwindCSS.
- **Go**: Standard library + Go-OpenAI for high-perf I/O.

