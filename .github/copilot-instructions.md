# Project Architecture & Guidelines

This project is a text-adventure game system composed of four distinct parts:
1.  **Agent Core** (`backroom_agent/`): Logic for the Game Master using LangGraph.
2.  **Backend** (`backend/`): FastAPI wrapper providing HTTP access to the agent.
3.  **Frontend** (`frontend/`): React + Vite terminal-style UI.
4.  **Data Pipeline** (`go_agent/`): High-concurrency Go service for batch scraping and processing Wiki data.

## Cross-Stack Data Protocol
The communication contract is strictly defined in `PROTOCOL.md`.
- **Python**: Models are in `backroom_agent/protocol.py` (Pydantic).
- **TypeScript**: Interfaces are in `frontend/src/types.ts`.
- **Rule**: Any change to the game state structure (e.g., adding a new stat) **MUST** be applied synchronously to `PROTOCOL.md`, `backroom_agent/protocol.py`, and `frontend/src/types.ts`.

## Agent Development (`backroom_agent/`)

### Agent Architecture
The agent system is modular, consisting of a main "DM Agent" and specialized "Subagents".
- **Main Agent**: `backroom_agent/agent.py` (Orchestrator).
- **Subagents**: Located in `backroom_agent/subagents/`.
- **Subagent State Pattern**:
    - `state.py`: TypedDict definition. **MUST** group keys by the Node that produces/updates them.
    - Example Structure:
      ```python
      class AgentState(TypedDict):
          # --- Input/Config ---
          ...
          # --- Node: fetch_content ---
          url: str
          html_content: str
          # --- Node: extract_items ---
          raw_items: List[dict]
      ```
- **Standard Subagent Structure**:
    - `state.py`: TypedDict definition for the subagent's internal state.
    - `nodes.py`: Atomic logic functions (Nodes) that modify the state.
    - `graph.py`: StateGraph construction and compilation.
    - `__init__.py`: Exports the compiled graph (e.g., `level_agent`).
    - **Examples**: `backroom_agent/subagents/level/`, `backroom_agent/subagents/event/`.

### Key Patterns
- **Prompts**: DO NOT hardcode prompts in Python.
    - Store prompts in `prompts/<name>.prompt`.
    - Load dynamically using `_load_system_prompt()` or `load_prompt()` utils.
    - **Standard Structure**: All prompts **MUST** follow the template defined in `backroom_agent/prompts/meta_prompt_optimizer.prompt`.
    - **Optimization**: Use `backroom_agent/prompts/meta_prompt_optimizer.prompt` to restructure unstructured instructions.
    - **Format Rules**: Use `backroom_agent/prompts/format_rules_generator.prompt` to generate strict schema constraints (JSON/SQL).
- **Search & Wiki**:
    - Use `backroom_agent/utils/search.py` for web searches (wraps `ddgs`).
    - Use `backroom_agent/tools/wiki_tools.py` for fetching/parsing Wiki HTML.
- **Vector Store**:
    - Use `backroom_agent/utils/vector_store.py` for local semantic search (Items, Levels).
    - **Note**: Uses a custom `numpy`/`pickle` implementation (avoid `chromadb` due to Python version conflicts).
- **Configuration**:
    - Access config via `backroom_agent.constants`.
    - NEVER use `os.getenv` directly in business logic (except in `constants.py`).

## Data Processing (`go_agent/`)
- **Purpose**: Batch processing of Backrooms Wiki pages to generate structured JSON data.
- **Execution**:
    - Batch: `go run main.go -batch -start 0 -end 20`
    - Single: `go run main.go -url <wiki_url>`
- **Concurrency**: Uses goroutines for parallel fetching. Be mindful of rate limits.

## Backend Development (`backend/`)
- **Entry Point**: `python backend/main.py` (Starts Uvicorn on port 8000).
- **Role**: Thin wrapper. It parses the frontend JSON, invokes the LangGraph agent, and returns the narrative + state diff.

## Frontend Development (`frontend/`)
- **State Management**: `App.tsx` is the source of truth for `attributes`, `vitals`, and `inventory`.
- **Network**: All API calls go to `http://localhost:8000/api/chat`.
- **Typing**: Always import types from `./types.ts`. Avoid `any`.
    - Example: `const data: ChatResponse = await response.json();`

## Workflows & Environment
- **Python Version**: **3.12** managed via `.venv`.
- **Scripts**: Use `scripts/` to run/test individual agents without the full server.
    - `python scripts/run_level_agent.py`: Test Level Agent (Fetching/Item Extraction).
    - `python scripts/run_agent.py`: Test Main DM Agent flow.
- **Testing**:
    - **Do not** use `scripts/extract_items.py` or `scripts/run_event_generator.py` (Deprecated/Deleted).
    - Prefer running the specific agent runner (e.g., `run_level_agent.py`) which invokes the graph.
- **Build Frontend**: `cd frontend && npm run build` (Checks TS types and builds assets).

