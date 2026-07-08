"""Settings loaded from environment variables."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    groq_api_key: str = ""
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    jina_api_key: str = ""
    environment: str = "development"
    similarity_threshold: float = 0.40
    embedding_model: str = "jina-embeddings-v3"
    embedding_dimensions: int = 1024
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 1024
    qdrant_collection: str = "parcerolegal"
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_missed_queries_table: str = "missed_queries"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    return Settings()
