# BackroomAgent Guidelines

## System Architecture
Text-adventure game system across four components:
1.  **Agent Core (`backroom_agent/`)**: LangGraph-based logic. Modular "Subagent" architecture (Level, Event, Suggestion).
2.  **Backend (`backend/`)**: FastAPI wrapper. Stateless execution of LangGraph agents per request.
3.  **Frontend (`frontend/`)**: React + Vite terminal UI.
4.  **Data Pipeline (`go_agent/`)**: High-concurrency Go service for scraping Wiki data into structured JSON.

## Critical Data Protocols
Strict type synchronization is enforced across the stack.
- **Protocol Definition**: `PROTOCOL.md` (Source of Truth).
- **Python Models**: `backroom_agent/protocol.py` (Pydantic).
- **TypeScript Types**: `frontend/src/types.ts` (Interfaces).
- **Go Structs**: `go_agent/agent/model/state.go` (Level Data Generation).
- **Rule**: Changes to game state, events, or level data structures **MUST** be applied synchronously across all 4 files.

## Subagent Pattern (`backroom_agent/subagents/`)
- **Structure**: Each subagent (e.g., `level/`) must have `state.py` (TypedDict), `nodes.py` (Logic), `graph.py` (StateGraph), and `__init__.py`.
- **State Definition**: In `state.py`, group keys by the Node that produces them (e.g., `# --- Node: fetch_content ---`).
- **Prompts**: Store in `prompts/*.prompt`. Never hardcode. Use `_load_system_prompt`.

## Data Pipeline (`go_agent/`)
- **Role**: Scrapes/cleans Wiki pages -> Generating structured Level JSONs -> extracting Items/Entities.
- **Level Data Structure**: `LevelData` struct in `state.go` defines the schema for `data/level/*.json`.
- **Run**: `go run main.go -name "Level 2"` (Single) or `-batch` (0-20).

## Workflows
- **Frontend**: `cd frontend && npm run dev`. Build: `npm run build`.
- **Backend API**: `python backend/main.py` (Port 8000).
- **Agent Testing**: Use `scripts/run_*.py` for isolated testing.
    - `python scripts/run_agent.py`: Test Main DM Agent.
    - `python scripts/run_level_agent.py`: Test Level Subagent.
- **Graph Viz**: `make graph` generates architecture diagrams in `tmp/`.

## Key Patterns & Utilities
- **Vector Store**: Custom `numpy`/`pickle` implementation in `backroom_agent/utils/vector_store.py`. Avoid `chromadb`.
- **Configuration**: Use `backroom_agent.constants`. NO `os.getenv` in logic.
- **Environment**: Python 3.12 (`.venv`).
- **Refs**: Item/Entity references in `analysis.py` are now lists of strings (Ids/Names), not full objects.

