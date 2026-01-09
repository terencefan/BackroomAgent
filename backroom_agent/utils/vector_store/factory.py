from typing import Any

from langchain_core.embeddings import Embeddings

from backroom_agent.constants import API_KEY, BASE_URL


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

        if not API_KEY:
            raise ValueError("API_KEY is missing. Please check your .env file.")

        print(f"Initializing OpenAI embedding model ({model_name})...")
        # Use api_key and base_url to be safe with newer versions, or ignore type if uncertain
        return OpenAIEmbeddings(
            model=model_name, api_key=API_KEY, base_url=BASE_URL  # type: ignore
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
