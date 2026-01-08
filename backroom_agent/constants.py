import os
from dotenv import load_dotenv

load_dotenv()

# Constants for LLM Configuration
API_KEY = os.getenv("OPENAI_API_KEY", "")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
