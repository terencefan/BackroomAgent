# Agent Nodes Architecture

This directory contains the individual functional units (Nodes) that make up the Backroom Agent's processing graph.

## Workflow Overview

The agent follows an event-driven workflow:
1.  **Router**: Determines the entry point.
2.  **Task Node**: Executes the specific logic for the event (Init, Item, or LLM).
3.  **Summary Node**: Updates game state (Time, Vitals, Inventory) and consolidates changes.
4.  **Suggestion Node**: Generates potential next actions for the player.

---

## Node Descriptions

### 1. `init_node` (`backroom_agent/nodes/init.py`)
- **Trigger**: `EventType.INIT`
- **Purpose**: Handles the start of a game session.
- **Action**: Returns the initial welcome message and sets up the narrative context.

### 2. `item_node` (`backroom_agent/nodes/item.py`)
- **Trigger**: `EventType.USE`, `EventType.DROP`
- **Purpose**: Manages inventory interactions.
- **Action**: precise logic for using or discarding items. It generates a narrative response describing the action's result (e.g., "You drank the Almond Water. +5 Sanity").

### 3. `llm_node` (`backroom_agent/nodes/llm.py`)
- **Trigger**: `EventType.MESSAGE` (and default fallback)
- **Purpose**: Handles open-ended roleplay and inputs that don't match specific mechanics.
- **Action**: Invokes the LLM (Large Language Model) with the system prompt and conversation history to generate a DM-style response.

### 4. `summary_node` (`backroom_agent/nodes/summary.py`)
- **Trigger**: *Always runs after a Task Node*
- **Purpose**: State management and consolidation.
- **Action**: 
    - Takes the current game state.
    - Applies internal game rules (e.g., incrementing time counter, passive stat decay).
    - Returns the updated `GameState` object which the backend will stream to the client.

### 5. `suggestion_node` (`backroom_agent/nodes/suggestion.py`)
- **Trigger**: *Always runs after Summary Node*
- **Purpose**: Player guidance.
- **Action**: Analyzes the new state and narrative context to generate a list of 2-4 clickable suggestions (e.g., "Run", "Hide", "Use Bandage") to help the UI.
