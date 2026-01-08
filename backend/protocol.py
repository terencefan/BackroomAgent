from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel


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
    quantity: int = 1
    description: Optional[str] = None
    category: Optional[str] = "resource"


class GameState(BaseModel):
    level: str
    time: int = 480  # Default to 8:00 AM (minutes from midnight)
    attributes: Attributes
    vitals: Vitals
    inventory: List[Optional[Item]]


class EventType(str, Enum):
    INIT = "init"
    ACTION = "action"
    MESSAGE = "message"
    USE = "use"
    DROP = "drop"


class GameEvent(BaseModel):
    type: EventType
    item_id: Optional[str] = None
    quantity: Optional[int] = None


class ChatRequest(BaseModel):
    event: GameEvent
    player_input: str
    current_state: Optional[GameState] = None


class BackendMessage(BaseModel):
    text: str
    sender: Literal["dm", "system"]
    options: Optional[List[str]] = None



class DiceRoll(BaseModel):
    type: Literal["d20", "d100"]
    result: int
    reason: Optional[str] = None


class StreamChunkType(str, Enum):
    MESSAGE = "message"
    DICE_ROLL = "dice_roll"
    STATE = "state"
    SUGGESTIONS = "suggestions"


class StreamChunkMessage(BaseModel):
    type: Literal[StreamChunkType.MESSAGE]
    text: str
    sender: Literal["dm", "system"]


class StreamChunkDice(BaseModel):
    type: Literal[StreamChunkType.DICE_ROLL]
    dice: DiceRoll


class StreamChunkState(BaseModel):
    type: Literal[StreamChunkType.STATE]
    state: GameState


class StreamChunkSuggestions(BaseModel):
    type: Literal[StreamChunkType.SUGGESTIONS]
    options: List[str]


class ChatResponse(BaseModel):
    messages: List[BackendMessage]
    new_state: GameState
    dice_roll: Optional[DiceRoll] = None

