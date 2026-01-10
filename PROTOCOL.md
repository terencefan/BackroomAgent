# Backend-Frontend Interaction Protocol

This document defines the JSON structure for communication between the React Frontend and the Python/FastAPI Backend.

## Endpoint

`POST /api/chat`

## Request Structure

The frontend sends the full game state along with the player's latest input.

```json
{
  "event": {
    "type": "message",            // "init", "action", "message", "use", "drop"
    "item_id": null,              // Optional: For 'use' or 'drop' events
    "quantity": null              // Optional: For 'drop' events
  },
  "player_input": "string",       // The text typed by the user
  "session_id": "string",         // Optional. UUID for session tracking
  "current_state": {              // Optional for 'init', required for others
    "level": "string",
    "time": 480,                  // Minutes from midnight
    "attributes": {
      "STR": "number",
      "DEX": "number",
      "CON": "number",
      "INT": "number",
      "WIS": "number",
      "CHA": "number"
    },
    "vitals": {
      "hp": "number",
      "maxHp": "number",
      "sanity": "number"
    },
    "inventory": [
      {
        "id": "string",
        "name": "string",
        "icon": "string",          // Optional emoji or icon key
        "quantity": "number",      // Optional, default 1
        "description": "string",   // Optional item description
        "category": "string"       // Optional: "resource", "weapon", "tool", "document", "medical", "special"
      },
      // ... null for empty slots
    ]
  }
}
```

## Streaming Response Protocol (NDJSON)

The backend streams the response as a sequence of JSON objects, each separated by a newline (`\n`).

### Stream Chunks

#### 1. Message Chunk
Standard narrative text.
```json
{
  "type": "message",
  "text": "The door handles are rusted shut.",
  "sender": "dm" // or "system"
}
```

#### 2. Init Chunk
Initialization narrative (Level Entry).
```json
{
  "type": "init",
  "text": "You noclip into Level 1..."
}
```

#### 3. State Update Chunk
Updates the client-side game state.
```json
{
  "type": "state",
  "state": { ... } // Full GameState object
}
```

#### 4. Logic Event Chunk (Pre-Dice)
Indicates a probabilistic event is about to happen (triggers UI wait state).
```json
{
  "type": "logic_event",
  "event": {
    "name": "Jump Scare",
    "die_type": "d100",
    "outcomes": [
      { "range": [1, 50], "result": { ... } }
    ]
  }
}
```

#### 5. Dice Roll Chunk
Triggers the visual dice roll animation.
```json
{
  "type": "dice_roll",
  "dice": {
    "type": "d20", // or "d6", "d100"
    "result": 18,
    "reason": "Strength Check"
  }
}
```

#### 6. Settlement Chunk (Post-Dice)
Visual log of state changes (Delta).
```json
{
  "type": "settlement",
  "delta": {
    "hp_change": -5,
    "sanity_change": 0,
    "items_added": ["Flashlight x1"],
    "items_removed": [],
    "level_transition": "Level 1" // Optional
  }
}
```

#### 7. Suggestions Chunk
Provides clickable options for the user.
```json
{
  "type": "suggestions",
  "options": ["Enter the room", "Listen at the door"]
}
```

## Models

### GameState
```typescript
interface GameState {
  level: string;
  time: number;
  attributes: Attributes;
  vitals: Vitals;
  inventory: (Item | null)[];
}
```

### EventType
```typescript
enum EventType {
  INIT = "init",
  ACTION = "action",
  MESSAGE = "message",
  USE = "use",
  DROP = "drop"
}
```
