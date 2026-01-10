import os

from dotenv import load_dotenv

load_dotenv()

# Constants for LLM Configuration
API_KEY = os.getenv("OPENAI_API_KEY", "")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# LangSmith Configuration
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT", "https://api.smith.langchain.com")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY", "")
LANGCHAIN_PROJECT = os.getenv("LANGCHAIN_PROJECT", "backroom-agent")


class GraphKeys:
    """Keys used in the State TypedDict and graph updates."""

    MESSAGES = "messages"
    EVENT = "event"
    USER_INPUT = "user_input"
    SESSION_ID = "session_id"
    CURRENT_GAME_STATE = "current_game_state"
    LOGIC_EVENT = "logic_event"
    LOGIC_OUTCOME = "logic_outcome"
    DICE_ROLL = "dice_roll"
    RAW_LLM_OUTPUT = "raw_llm_output"
    LEVEL_CONTEXT = "level_context"
    VALID_ACTIONS = "valid_actions"
    SUGGESTIONS = "suggestions"


class NodeConstants:
    """Keys/Names for Graph Nodes."""

    ROUTER_NODE = "router_node"
    INIT_NODE = "init_node"
    ITEM_NODE = "item_node"
    ITEM_RESOLVE_NODE = "item_resolve_node"
    SIMPLE_CHAT = "simple_chat"
    EVENT_NODE = "event_node"
    DICE_NODE = "dice_node"
    DICE_RESOLVE_NODE = "dice_resolve_node"
    EVENT_RESOLVE_NODE = "event_resolve_node"
    SETTLEMENT_NODE = "settlement_node"
    SUMMARY_NODE = "summary_node"
    SUGGESTION_NODE = "suggestion_node"
