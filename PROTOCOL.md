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
  "message": "string",            // The DM's narrative response to display in chat
  "sender": "dm",                 // Usually "dm", but could be "system"
  "new_state": {                  // The updated state key-values
    "vitals": {                   // Only fields that changed need to be returned, or return full object
      "hp": 15,
      ...
    },
    "inventory": [ ... ]          // Updated inventory if items were used/gained
  }
}
```

## Types

### GameState
```typescript
interface GameState {
  level: string;
  attributes: Attributes;
  vitals: Vitals;
  inventory: (Item | null)[];
}
```
