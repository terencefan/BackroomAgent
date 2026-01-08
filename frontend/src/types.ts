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
}

export interface GameState {
  level: string;
  attributes: Attributes;
  vitals: Vitals;
  inventory: (Item | null)[];
}

export interface ChatRequest {
  player_input: string;
  current_state: GameState;
}

export interface ChatResponse {
  message: string;
  sender: 'dm' | 'system';
  new_state?: GameState;
}
