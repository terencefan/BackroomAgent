from typing import Any

from langchain_core.embeddings import Embeddings

from backroom_agent.constants import (DEEPSEEK_API_KEY, DEEPSEEK_BASE_URL,
                                      OPENAI_API_KEY)


def get_embedding_model(
    provider: str = "local", model_name: str = "all-MiniLM-L6-v2"
) -> Embeddings:
    """
    Factory function to get the embedding model based on provider and model name.

    Args:
        provider (str): "local" (HuggingFace) or "openai".
        model_name (str): The name of the model to use.
    """
    if provider == "openai":
        try:
            from langchain_openai import OpenAIEmbeddings
        except ImportError:
            raise ImportError("Missing dependencies: pip install langchain-openai")

        # Use DEEPSEEK_API_KEY or OPENAI_API_KEY as fallback
        api_key = DEEPSEEK_API_KEY or OPENAI_API_KEY
        if not api_key:
            raise ValueError(
                "API key is missing. Please set DEEPSEEK_API_KEY or OPENAI_API_KEY in your .env file."
            )

        print(f"Initializing OpenAI embedding model ({model_name})...")
        # Use api_key and base_url to be safe with newer versions, or ignore type if uncertain
        return OpenAIEmbeddings(
            model=model_name, api_key=api_key, base_url=DEEPSEEK_BASE_URL  # type: ignore
        )
    else:  # local / huggingface
        try:
            from langchain_huggingface import HuggingFaceEmbeddings
        except ImportError:
            raise ImportError(
                "Missing dependencies: pip install langchain-huggingface sentence-transformers scikit-learn"
            )
        print(f"Initializing local embedding model ({model_name})...")
        return HuggingFaceEmbeddings(model_name=model_name)
