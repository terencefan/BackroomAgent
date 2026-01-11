# Backroom Agent System Architecture

This document visualizes the internal logic of the Backroom Agent Game Engine, covering both the Python Backend (Logic Core) and the Typescript Frontend (State Management).

## 1. System Overview

The system consists of a React Frontend that communicates with a FastAPI Python Backend via HTTP Streaming (NDJSON).

```mermaid
graph TD
    User([Player]) <-->|Interacts| FE[Frontend (React/Vite)]
    
    subgraph "Frontend Engine (useGameEngine)"
        FE_Queue[Event Queue]
        FE_State[Game State]
        FE_Logic[Logic/Dice Lock]
    end
    
    FE <-->|HTTP Stream (NDJSON)| API[FastAPI Server]
    
    subgraph "Backend Agent (Python)"
        API <--> Router[Router Node]
        Router --> Graph[LangGraph Agent]
        Graph <--> Tools[Tools / Vector Store]
        Graph <--> Memory[Redis Memory]
    end
    
    Graph <-->|Inference| LLM[LLM (GPT-4)]
```

## 2. Backend Game Loop (LangGraph)

The core narrative logic runs on a directed cyclic graph. It decides whether to just generate text, perform a dice roll (Logic Event), or resolve the turn.

```mermaid
stateDiagram-v2
    [*] --> RouterNode
    
    state "Router" as RouterNode
    state "Event Generation (LLM)" as EventNode
    state "Dice Roll (Mechanics)" as DiceNode
    state "Resolve & Update" as ResolveNode
    state "Summary & Suggestions" as SummaryNode
    
    RouterNode --> EventNode: Type = Event/Message
    RouterNode --> InitNode: Type = Init
    
    EventNode --> CheckDice: Did LLM generate a Logic Event?
    
    state CheckDice <<choice>>
    CheckDice --> DiceNode: Yes (e.g., "Listen", "Attack")
    CheckDice --> ResolveNode: No (Pure Narrative)
    
    DiceNode --> ResolveNode: Pass Roll Result
    
    state CheckLoop <<choice>>
    ResolveNode --> CheckLoop: Suggestions ready?
    
    CheckLoop --> SummaryNode: Yes (Turn Complete)
    CheckLoop --> EventNode: No (Loop back for reaction)
    
    SummaryNode --> [*]
```

## 3. Frontend Streaming & Logic Lock

The Frontend `useGameEngine` hook acts as a specialized state machine that handles the asynchronous stream while enforcing narrative pacing (preventing spoilers).

### The Logic Lock Mechanism

This ensures the user sees the **Dice Animation** *after* the **Challenge** is presented but *before* the **Result** is revealed.

```mermaid
sequenceDiagram
    participant BE as Backend Stream
    participant Q as Frontend Queue
    participant UI as Chat UI
    participant Lock as Logic Lock
    participant Dice as Waiting Dice
    
    Note over BE, UI: SCENARIO: A Logic Event Occurs
    
    BE->>Q: 1. Logic Event Chunk (Challenge)
    Q->>UI: Show "Challenge: Listen with D20"
    UI->>Lock: ACTIVATE LOCK (MsgID)
    Note right of Lock: Queue is now BLOCKED for narrative/state
    
    BE->>Q: 2. Message Chunk (Narrative Result)
    Q->>Q: BLOCKED by Lock (Waits)
    
    BE->>Q: 3. Dice Roll Chunk (Result=15)
    Q->>Dice: Allowed through! Stored in Pending Dice
    
    BE->>Q: 4. Settlement Chunk (HP -5)
    Q->>Q: BLOCKED by Lock (Prevents Spoiler)
    
    Note over UI: User sees "Click to Roll" button
    User->>UI: Clicks "Roll"
    UI->>Lock: Confirm MsgID
    Lock->>Dice: Check Pending?
    Dice->>UI: Trigger Animation (Rolls 15)
    
    Note over UI: Animation Completes
    UI->>Lock: RELEASE LOCK
    
    Lock->>Q: Resume Processing
    Q->>UI: Process (2) Narrative Result
    Q->>UI: Process (4) Settlement Updates
```

## 4. Frontend Queue Logic (Detailed)

How the `tryProcessQueue` function decides what to process next.

```mermaid
flowchart TD
    Start[New Chunk Arrives / Animation Ends] --> Enqueue[Add to PendingQueue]
    Enqueue --> IsAnimating{Is UI Animating?}
    
    IsAnimating -- Yes --> Wait[Wait]
    IsAnimating -- No --> CheckLock{Is Logic Lock Active?}
    
    CheckLock -- No --> Process[Process Chunk]
    CheckLock -- Yes --> CheckType{Chunk Type?}
    
    CheckType -- DICE_ROLL --> ProcessDice[Cache Pending Dice / Trigger Animation]
    ProcessDice --> Process
    
    CheckType -- Other --> Block[Block & Wait for Lock Release]
    
    Process --> UpdateState[Update React State]
    UpdateState --> Render[Render UI]
```
