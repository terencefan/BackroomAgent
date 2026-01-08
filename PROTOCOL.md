# Backend-Frontend Interaction Protocol

This document defines the JSON structure for communication between the React Frontend and the Python/FastAPI Backend.

## Endpoint

`POST /api/chat`

## Request Structure

The frontend sends the full game state along with the player's latest input. This allows the backend to be stateless (or semi-stateless) and just process the transition.

```json
{
  "event": {
    "type": "init"                // "init", "action", or "message"
  },
  "player_input": "string",       // The text typed by the user (e.g., "Look around", "Use Key")
  "current_state": {              // Optional for 'init', required for 'action'
    "level": "string",            // Current Level ID (e.g., "Level 1")
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
      "sanity": "number",
      "maxSanity": "number"
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

## Response Structure

The backend calculates the consequences of the action and returns the *diff* or the *new state* along with the narrative response.

```json
{
  "messages": [
    {
      "text": "string",
      "sender": "dm"
    }
  ],
  "new_state": {                  // The updated state
    "vitals": {
      "hp": 15,
      ...
    },
    // ...
  },
  "dice_roll": {                  // Optional: Dice result
    "type": "d20",                // "d20" or "d100"
    "result": 18,
    "target": 12,                 // Optional target/DC
    "reason": "Dexterity Check"   // Optional context
  }
}
```

## Types

### DiceRoll
```typescript
interface DiceRoll {
  type: 'd20' | 'd100';
  result: number;
  reason?: string;
}
```

## Streaming Response Protocol (NDJSON)

The backend now streams the response as a sequence of JSON objects, each separated by a newline (`\n`). This allows for progressive UI updates (e.g., showing a dice roll before the final narrative).

### Stream Chunks

#### 1. Message Chunk
Explains the context or provides narrative.
```json
{
  "type": "message",
  "text": "The door handles are rusted shut. You try to force them.",
  "sender": "dm"
}
```

#### 2. Dice Roll Chunk (Optional)
Triggers the visual dice roll.
```json
{
  "type": "dice_roll",
  "dice": {
    "type": "d20",
    "result": 18,
    "reason": "Strength Check"
  }
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

#### 4. Suggestions Chunk (Optional)
Provides clickable options for the user.
```json
{
  "type": "suggestions",
  "options": ["Enter the room", "Listen at the door"]
}
```
```typescript
interface GameState {
  level: string;
  attributes: Attributes;
  vitals: Vitals;
  inventory: (Item | null)[];
}
```
