from backroom_agent.constants import API_KEY, BASE_URL

# Try to import dependencies for type checking or simple referencing,
# but main imports are inside get_embedding_model to handle missing deps.
try:
    from langchain_huggingface import HuggingFaceEmbeddings
    from langchain_openai import OpenAIEmbeddings
except ImportError:
    HuggingFaceEmbeddings = None
    OpenAIEmbeddings = None


def get_embedding_model(provider: str = "local", model_name: str = "all-MiniLM-L6-v2"):
    """
    Factory function to get the embedding model based on provider and model name.

    Args:
        provider (str): "local" (HuggingFace) or "openai".
        model_name (str): The name of the model to use.
    """
    if provider == "openai":
        if OpenAIEmbeddings is None:
            raise ImportError("Missing dependencies: pip install langchain-openai")
        if not API_KEY:
            raise ValueError("API_KEY is missing. Please check your .env file.")

        print(f"Initializing OpenAI embedding model ({model_name})...")
        return OpenAIEmbeddings(
            model=model_name, openai_api_key=API_KEY, openai_api_base=BASE_URL
        )
    else:  # local / huggingface
        if HuggingFaceEmbeddings is None:
            raise ImportError(
                "Missing dependencies: pip install langchain-huggingface sentence-transformers scikit-learn"
            )
        print(f"Initializing local embedding model ({model_name})...")
        return HuggingFaceEmbeddings(model_name=model_name)
