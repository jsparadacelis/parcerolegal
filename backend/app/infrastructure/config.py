"""Settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str = ""
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    environment: str = "development"
    similarity_threshold: float = 0.65
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    llm_model: str = "llama-3.1-70b-versatile"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 1024
    qdrant_collection: str = "parcerolegal"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    return Settings()
