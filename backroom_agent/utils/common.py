import os
from langchain_openai import ChatOpenAI
from langchain_core.language_models import BaseChatModel
from backroom_agent.constants import API_KEY, BASE_URL, MODEL_NAME

def get_project_root() -> str:
    """Returns the absolute path to the project root directory."""
    # current file: backroom_agent/utils/__init__.py or common.py
    # Assuming this file is at backroom_agent/utils/common.py
    # and project root is two levels up from backroom_agent
    
    # Path of this file: .../backroom_agent/utils/common.py
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # Parent of utils: .../backroom_agent
    backroom_agent_dir = os.path.dirname(current_dir)
    
    # Parent of backroom_agent: .../ProjectRoot
    project_root = os.path.dirname(backroom_agent_dir)
    
    return project_root

def get_prompt_path(prompt_name: str) -> str:
    """Returns the absolute path to a prompt file."""
    root = get_project_root()
    return os.path.join(root, "prompts", prompt_name)

def load_prompt(prompt_name: str) -> str:
    """Loads the content of a prompt file."""
    path = get_prompt_path(prompt_name)
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def get_llm() -> BaseChatModel:
    """Return a chat model based on configuration."""
    if not API_KEY:
        raise ValueError("API_KEY is missing. Please check your .env file.")

    return ChatOpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        model=MODEL_NAME
    )
