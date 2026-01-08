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
  maxSanity: number;
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

export interface ChatRequest {
  event: GameEvent;
  player_input: string;
  current_state: GameState | null;
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
  type: 'd20' | 'd100';
  result: number;
  reason?: string;
}

export const StreamChunkType = {
  MESSAGE: 'message',
  DICE_ROLL: 'dice_roll',
  STATE: 'state',
  SUGGESTIONS: 'suggestions'
} as const;

export type StreamChunkType = typeof StreamChunkType[keyof typeof StreamChunkType];

export interface StreamChunkMessage {
  type: typeof StreamChunkType.MESSAGE;
  text: string;
  sender: 'dm' | 'system';
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


export type StreamChunk = 
  | StreamChunkMessage 
  | StreamChunkDice 
  | StreamChunkState 
  | StreamChunkSuggestions;

export interface ChatResponse {
  messages: BackendMessage[];
  new_state: GameState;
  dice_roll?: DiceRoll;
}


export interface Message {
  id: number;
  sender: 'dm' | 'player' | 'system';
  text: string;
  options?: string[];
}
