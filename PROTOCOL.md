# Backend-Frontend Interaction Protocol

This document defines the SSE (Server-Sent Events) streaming protocol for communication between the React Frontend and the Python/FastAPI Backend.

## Endpoint

`POST /api/chat/stream`

## Protocol Overview

The protocol uses SSE (Server-Sent Events) for streaming responses. The key optimization is that:
- **init 事件**：建立连接时发送完整上下文（重建会话）
- **message 事件**：只发送增量（player_input + game_state），消息历史由服务器端维护

## Request Structure

### Init Event (建立连接，重建会话)

```json
{
  "event": {
    "type": "init"
  },
  "session_id": "session-xxx",
  "game_state": {
    "level": "Level 0",
    "time": 480,
    "attributes": {
      "STR": 10,
      "DEX": 10,
      "CON": 10,
      "INT": 10,
      "WIS": 10,
      "CHA": 10
    },
    "vitals": {
      "hp": 10,
      "maxHp": 10,
      "sanity": 100
    },
    "inventory": []
  }
}
```

**行为**：
- 创建新会话或重置已有会话（清空消息历史，重新开始）
- 建立 SSE 连接
- 发送完整上下文（此时消息历史为空，只有初始游戏状态）
- 处理 init 事件，保存产生的消息到会话

### Message Event (后续交互，复用会话)

```json
{
  "event": {
    "type": "message"
  },
  "player_input": "用户输入的新消息",
  "session_id": "session-xxx",
  "game_state": {
    "level": "Level 1",
    "time": 500,
    "attributes": { ... },
    "vitals": { ... },
    "inventory": [ ... ]
  }
}
```

**行为**：
- 复用已有会话（使用会话中的消息历史）
- 只发送增量（player_input + game_state），**不包含消息历史**
- 使用历史消息 + 新消息构建完整上下文
- 处理 message 事件，保存新消息到会话

**关键点**：
- 消息历史由服务器端维护，前端不需要传递
- 每次 init 事件都会重建会话（清空历史）
- message 事件复用会话（保持对话连续性）

## SSE Streaming Response Protocol

The backend streams the response as Server-Sent Events (SSE) format: `data: {json}\n\n`

### Response Chunks

#### 1. Init Context Chunk (仅 init 事件)
发送完整上下文（建连时的第一个消息）

```json
data: {
  "type": "init_context",
  "messages": [
    { "type": "ai", "content": "..." },
    { "type": "human", "content": "..." }
  ],
  "game_state": { ... }
}
```

#### 2. Init Chunk
初始化叙事文本（仅 init 事件）

```json
data: {
  "type": "init",
  "text": "You noclip into Level 1..."
}
```

#### 3. Message Chunk
标准叙事文本（message 事件）

```json
data: {
  "type": "message",
  "text": "The door handles are rusted shut.",
  "sender": "dm" // or "system"
}
```

#### 4. State Update Chunk
更新客户端游戏状态

```json
data: {
  "type": "state",
  "state": { ... } // Full GameState object
}
```

#### 5. Logic Event Chunk (Pre-Dice)
指示概率事件即将发生（触发 UI 等待状态）

```json
data: {
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

#### 6. Dice Roll Chunk
触发视觉骰子动画

```json
data: {
  "type": "dice_roll",
  "dice": {
    "type": "d20", // or "d6", "d100"
    "result": 18,
    "reason": "Strength Check"
  }
}
```

#### 7. Settlement Chunk (Post-Dice)
状态变更的可视化日志（Delta）

```json
data: {
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

#### 8. Suggestions Chunk
提供可点击的选项

```json
data: {
  "type": "suggestions",
  "options": ["Enter the room", "Listen at the door"]
}
```

## Session Management

### 会话生命周期

- **创建/重置**：init 事件时（总是创建新会话或重置已有会话，清空消息历史）
- **复用**：message 事件时（使用已有会话的消息历史）
- **更新**：每次事件交互后（保存新消息和游戏状态）
- **过期**：24 小时无活动后自动清理（Redis TTL）
- **清理**：显式断开连接或超时

### 会话状态流转

```
init 事件 → 创建/重置会话（消息历史 = []）
         → 处理 init → 保存消息到会话（消息历史 = [init 相关消息]）

message 事件 1 → 获取会话（消息历史 = [init 相关消息]）
              → 处理 message 1 → 保存消息到会话（消息历史 = [init, message 1]）

message 事件 2 → 获取会话（消息历史 = [init, message 1]）
              → 处理 message 2 → 保存消息到会话（消息历史 = [init, message 1, message 2]）

init 事件（再次） → 重置会话（消息历史 = []，重新开始）
```

## Data Models

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

### StreamInitRequest
```typescript
interface StreamInitRequest {
  event: GameEvent; // type must be "init"
  session_id?: string;
  game_state?: GameState | null;
}
```

### StreamMessageRequest
```typescript
interface StreamMessageRequest {
  event: GameEvent; // type must be "message"
  player_input: string;
  session_id?: string;
  game_state?: GameState | null; // 只发送增量
}
```

## Advantages

1. **减少数据传输**：不再每次发送完整上下文
2. **降低 LLM token 消耗**：后端维护消息历史，只发送增量
3. **更好的用户体验**：SSE 流式响应减少延迟
4. **支持断线重连**：Redis 持久化支持恢复会话

## Implementation Notes

- SSE 格式：`data: {json}\n\n`
- 响应类型：`text/event-stream`
- 连接管理：每次请求建立新的 SSE 连接（POST 请求返回 SSE 流）
- 会话存储：内存 + Redis 持久化（混合模式）
