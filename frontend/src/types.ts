export interface Attributes {
  STR: number;
  DEX: number;
  CON: number;
  INT: number;
  WIS: number;
  CHA: number;
}

export interface Vitals {
  hp: number;
  maxHp: number;
  sanity: number;
}

export interface Item {
  id: string;
  name: string;
  icon?: string;
  quantity?: number;
  description?: string;
  category?: 'resource' | 'weapon' | 'tool' | 'document' | 'medical' | 'special';
}

export interface GameState {
  level: string;
  time: number;
  attributes: Attributes;
  vitals: Vitals;
  inventory: (Item | null)[];
}

export const EventType = {
  INIT: 'init',
  ACTION: 'action',
  MESSAGE: 'message',
  USE: 'use',
  DROP: 'drop'
} as const;

export type EventType = typeof EventType[keyof typeof EventType];

export interface GameEvent {
  type: EventType;
  item_id?: string;
  quantity?: number;
}

// Legacy ChatRequest (deprecated)
export interface ChatRequest {
  event: GameEvent;
  player_input: string;
  session_id?: string;
  current_state: GameState | null;
}

// New SSE Stream Request Models
export interface StreamInitRequest {
  event: GameEvent; // type must be "init"
  session_id?: string;
  game_state?: GameState | null; // 初始游戏状态
}

export interface StreamMessageRequest {
  event: GameEvent; // type must be "message"
  player_input: string;
  session_id?: string;
  game_state?: GameState | null; // 当前游戏状态（增量）
}

export interface BackendMessage {
  text: string;
  sender: 'dm' | 'system';
  options?: string[];
}

export type UIEvent =
  | { type: 'SHOW_MESSAGE'; message: BackendMessage }
  | { type: 'UPDATE_VITALS'; vitals: Vitals }
  | { type: 'UPDATE_INVENTORY'; inventory: (Item | null)[] }
  | { type: 'UPDATE_ATTRIBUTES'; attributes: Attributes }
  | { type: 'UNLOCK_INTERACTION' };


export interface DiceRoll {
  type: 'd6' | 'd20' | 'd100';
  result: number;
  reason?: string;
}

export const StreamChunkType = {
  MESSAGE: 'message',
  DICE_ROLL: 'dice_roll',
  STATE: 'state',
  SUGGESTIONS: 'suggestions',
  LOGIC_EVENT: 'logic_event',
  INIT: 'init',
  SETTLEMENT: 'settlement',
  INIT_CONTEXT: 'init_context',
} as const;

export type StreamChunkType = typeof StreamChunkType[keyof typeof StreamChunkType];

export interface SettlementDelta {
    hp_change: number;
    sanity_change: number;
    items_added: string[];
    items_removed: string[];
    level_transition?: string;
}

export interface StreamChunkSettlement {
    type: typeof StreamChunkType.SETTLEMENT;
    delta: SettlementDelta;
}

export interface StreamChunkInitContext {
    type: typeof StreamChunkType.INIT_CONTEXT;
    messages: Array<{ type: string; content: string }>; // 历史消息
    game_state?: GameState | null; // 当前游戏状态
}


export interface EventOutcome {
  range: number[];
  result: {
    content: string;
    updated_state_diff?: Partial<GameState>;
  };
}

export interface LogicEvent {
  name: string;
  die_type: 'd6' | 'd20' | 'd100';
  outcomes: EventOutcome[];
}

export interface StreamChunkMessage {
  type: typeof StreamChunkType.MESSAGE;
  text: string;
  sender: 'dm' | 'system';
  logicEvent?: LogicEvent;
  options?: string[];
}

export interface StreamChunkInit {
  type: typeof StreamChunkType.INIT;
  text: string;
}

export interface StreamChunkDice {
  type: typeof StreamChunkType.DICE_ROLL;
  dice: DiceRoll;
}

export interface StreamChunkState {
  type: typeof StreamChunkType.STATE;
  state: GameState;
}

export interface StreamChunkSuggestions {
  type: typeof StreamChunkType.SUGGESTIONS;
  options: string[];
}

export interface StreamChunkLogicEvent {
  type: typeof StreamChunkType.LOGIC_EVENT;
  event: LogicEvent;
}


export type StreamChunk = 
  | StreamChunkMessage 
  | StreamChunkDice 
  | StreamChunkState 
  | StreamChunkSuggestions
  | StreamChunkLogicEvent
  | StreamChunkInit
  | StreamChunkSettlement
  | StreamChunkInitContext;

export interface ChatResponse {
  messages: BackendMessage[];
  new_state: GameState;
  dice_roll?: DiceRoll;
}


export interface Message {
  id: number;
  sender: 'dm' | 'player' | 'system' | 'init';
  text: string;
  options?: string[];
  selectedOption?: string;
  logicEvent?: LogicEvent;
  logicEventConfirmed?: boolean;
  logicRollResult?: number;
  settlement?: SettlementDelta; // For rendering visual logs
}
