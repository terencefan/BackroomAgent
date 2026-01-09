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
- **Backend Server**: `python -m backroom_agent.server` (runs on port 8000). (Use `make server`)
- **Frontend**: `cd frontend && npm run dev` (runs on port 5173). (Use `make client`)
- **Agent Testing**: Use `scripts/` to run agents in isolation without the server.
    - `python scripts/run_agent.py`: Interactive DM loop.
- **Graph Visualization**: `make graph` runs generation scripts to output Mermaid/PNG graphs in `tmp/`.
- **Formatting**: `make format` runs black, isort, and eslint.

## Key Code Patterns

### LangGraph Control Flow (`backroom_agent/graph.py`)
The game loop is defined as a directed graph:
1.  **Router Node**: Prefetches context (HTML) but delegates decision to `route_event`.
2.  **Task Nodes**: `Init`, `Inventory`, `Generate` (Main LLM logic).
3.  **Process Node**: Parses LLM output and checks for `LogicEvent`.
4.  **Dice Node** (Conditional): Executes `d6`/`d20`/`d100` rolls if detected from `LogicEvent`.
    - Loop logic: Dice output feeds back into `Generate` node for narrative resolution.
5.  **Summary Node** (`NODE_SUMMARY`): Standardizes outputs before end.

### Frontend Logic Locking (`useGameEngine.ts`)
To prevent spoilers (narrative appearing before dice animation finishes), the frontend employs a **Queue Locking Mechanism**:
- `lastLogicMsgIdRef` tracks active logic/dice events.
- `tryProcessQueue` **blocks** incoming `MESSAGE`, `STATE`, and `SUGGESTION` chunks if a Logic Event is pending confirmation.
- Only `DICE_ROLL` chunks are allowed through the lock to prepare the animation.
- The stream resumes only after the animation completes.

### Dice Mechanics
- Supported Types: `d6` (Simple), `d20` (Standard), `d100` (Rare).
- Logic is handled in `backroom_agent/nodes/dice.py`.
- Animations in `frontend/src/components/DiceAnimation.tsx`.

## Best Practices
- **Configuration**: Use `backroom_agent.constants`. Avoid `os.getenv` in business logic.
- **Prompts**: Store in `backroom_agent/prompts/*.prompt`. Never hardcode.
- **Vector Store**: internal `numpy`/`pickle` impl in `backroom_agent/utils/vector_store.py`.
- **References**: Item/Entity refs in analysis tools are strings (IDs), not objects.

## Tech Stack Details
- **Python**: 3.12+, LangGraph, FastAPI, Pydantic.
- **Frontend**: React, TypeScript, TailwindCSS.
- **Go**: Standard library + Go-OpenAI for high-perf I/O.

