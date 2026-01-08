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

export interface ChatResponse {
  messages: BackendMessage[];
  new_state: GameState;
}

export interface Message {
  id: number;
  sender: 'dm' | 'player' | 'system';
  text: string;
}
