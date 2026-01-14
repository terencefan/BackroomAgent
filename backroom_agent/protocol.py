from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


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


# Legacy ChatRequest (deprecated, will be removed)
class ChatRequest(BaseModel):
    event: GameEvent
    player_input: str
    session_id: Optional[str] = None
    current_state: Optional[GameState] = None


# New SSE Stream Request Models
class StreamInitRequest(BaseModel):
    """init 事件请求：建立 SSE 连接，重建会话"""

    event: GameEvent  # type must be "init"
    session_id: Optional[str] = None
    game_state: Optional[GameState] = None  # 初始游戏状态


class StreamMessageRequest(BaseModel):
    """message 事件请求：后续交互，只发送增量"""

    event: GameEvent  # type must be "message"
    player_input: str
    session_id: Optional[str] = None
    game_state: Optional[GameState] = None  # 当前游戏状态（增量）


class BackendMessage(BaseModel):
    text: str
    sender: Literal["dm", "system"]
    options: Optional[List[str]] = None


class DiceRoll(BaseModel):
    type: Literal["d6", "d20", "d100"]
    result: int
    reason: Optional[str] = None


class StreamChunkType(str, Enum):
    MESSAGE = "message"
    DICE_ROLL = "dice_roll"
    STATE = "state"
    SUGGESTIONS = "suggestions"
    LOGIC_EVENT = "logic_event"
    INIT = "init"
    SETTLEMENT = "settlement"
    INIT_CONTEXT = "init_context"


class EventOutcome(BaseModel):
    range: List[int]
    result: Dict[str, Any]


class LogicEvent(BaseModel):
    name: str
    die_type: Literal["d6", "d20", "d100"]
    outcomes: List[EventOutcome]


class SettlementDelta(BaseModel):
    hp_change: int = 0
    sanity_change: int = 0
    items_added: List[str] = []  # formatted strings like "Name xQty"
    items_removed: List[str] = []
    level_transition: Optional[str] = None


class StreamChunkSettlement(BaseModel):
    type: Literal[StreamChunkType.SETTLEMENT]
    delta: SettlementDelta


class StreamChunkMessage(BaseModel):
    type: Literal[StreamChunkType.MESSAGE]
    text: str
    sender: Literal["dm", "system"]


class StreamChunkInit(BaseModel):
    type: Literal[StreamChunkType.INIT]
    text: str


class StreamChunkDice(BaseModel):
    type: Literal[StreamChunkType.DICE_ROLL]
    dice: DiceRoll


class StreamChunkState(BaseModel):
    type: Literal[StreamChunkType.STATE]
    state: GameState


class StreamChunkSuggestions(BaseModel):
    type: Literal[StreamChunkType.SUGGESTIONS]
    options: List[str]


class StreamChunkLogicEvent(BaseModel):
    type: Literal[StreamChunkType.LOGIC_EVENT]
    event: LogicEvent


class StreamChunkInitContext(BaseModel):
    """初始化上下文：建连时通过 SSE 发送完整上下文"""

    type: Literal[StreamChunkType.INIT_CONTEXT]
    messages: List[Dict[str, Any]]  # 历史消息（序列化后的字典）
    game_state: Optional[GameState] = None  # 当前游戏状态


class ChatResponse(BaseModel):
    messages: List[BackendMessage]
    new_state: GameState
    dice_roll: Optional[DiceRoll] = None


# --- Level Data Models (Matches Go Structs) ---


class SurvivalDifficulty(BaseModel):
    class_: str = Field(alias="class")  # 'class' is a keyword in Python
    description: str


class Atmosphere(BaseModel):
    visuals: List[str]
    audio: List[str]
    smell: List[str]
    vibe: List[str]


class EnvironmentalMechanic(BaseModel):
    mechanic: str
    effect: str
    trigger_probability: str


class SubZone(BaseModel):
    name: str
    description: str
    danger_level: str


class Faction(BaseModel):
    name: str
    alignment: str
    description: str
    population: str


class POI(BaseModel):
    name: str
    description: str
    access_probability: str


class Entrance(BaseModel):
    method: str
    from_: Optional[str] = Field(None, alias="from")  # 'from' is a keyword


class Exit(BaseModel):
    method: str
    condition: str
    next: Optional[str]


class Transitions(BaseModel):
    entrances: List[Entrance]
    exits: List[Exit]


class LevelEvent(BaseModel):
    event: str
    probability: str


class Link(BaseModel):
    text: str
    url: str


class LevelEntity(BaseModel):
    id: str
    name: str
    description: str
    behavior: str


class LevelItem(BaseModel):
    id: str
    name: str
    description: str
    category: str


class LevelData(BaseModel):
    level_id: str
    title: Optional[str]
    survival_difficulty: SurvivalDifficulty
    atmosphere: Atmosphere
    environmental_mechanics: List[EnvironmentalMechanic]
    sub_zones: List[SubZone]
    factions: List[Faction]
    pois: List[POI]
    transitions: Transitions
    events: List[LevelEvent]
    links: Optional[List[Link]] = None
    items: Optional[List[str]] = None  # New format: list of names
    entities: Optional[List[str]] = None  # New format: list of names
    # Legacy/Full Load support
    findable_items: Optional[List[LevelItem]] = None
    entities_list: Optional[List[LevelEntity]] = Field(
        None, alias="entities"
    )  # Handle potential conflict if raw list of dicts
