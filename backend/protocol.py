from pydantic import BaseModel
from typing import List, Optional, Literal

class Attributes(BaseModel):
    STR: int
    DEX: int
    CON: int
    INT: int
    WIS: int
    CHA: int

class Vitals(BaseModel):
    hp: int
    maxHp: int
    sanity: int
    maxSanity: int

class Item(BaseModel):
    id: str
    name: str
    icon: Optional[str] = None

class GameState(BaseModel):
    level: str
    attributes: Attributes
    vitals: Vitals
    inventory: List[Optional[Item]]

class ChatRequest(BaseModel):
    player_input: str
    current_state: GameState

class ChatResponse(BaseModel):
    message: str
    sender: Literal["dm", "system"]
    new_state: Optional[GameState] = None
