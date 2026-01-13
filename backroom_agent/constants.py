import os

from dotenv import load_dotenv

load_dotenv()

# Constants for LLM Configuration
# Each provider has its own API key
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DOUBAO_API_KEY = os.getenv("DOUBAO_API_KEY", "")

# Provider-specific base URLs and model names
DEEPSEEK_BASE_URL = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

DOUBAO_BASE_URL = os.getenv(
    "DOUBAO_BASE_URL", "https://ark.cn-beijing.volces.com/api/v3"
)
DOUBAO_MODEL = os.getenv("DOUBAO_MODEL", "ep-20241230123456-abcde")

# Legacy support: OPENAI_API_KEY for backward compatibility
# If set, it will be used as fallback when provider-specific key is missing
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

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
    SETTLEMENT_DELTA = "settlement_delta"


class NodeConstants:
    """Keys/Names for Graph Nodes."""

    ROUTER_NODE = "router_node"
    INIT_NODE = "init_node"
    ITEM_NODE = "item_node"
    ITEM_RESOLVE_NODE = "item_resolve_node"
    SIMPLE_CHAT = "simple_chat"
    EVENT_NODE = "event_node"
    DICE_NODE = "dice_node"
    RESOLVE_NODE = "resolve_node"
    SUMMARY_NODE = "summary_node"
    SUGGESTION_NODE = "suggestion_node"
