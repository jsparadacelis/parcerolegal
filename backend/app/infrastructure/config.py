"""Settings loaded from environment variables + fixed backend constants.

Este módulo centraliza toda la configuración del backend:

- `Settings`: valores que dependen del entorno (secretos, endpoints tuneables,
  parámetros del pipeline). Se sobreescriben con variables de entorno / `.env`.
- Constantes de módulo: literales fijos del protocolo/proveedor que no cambian
  entre entornos (URLs de las APIs externas, códigos HTTP, límites de validación,
  metadatos de la API). Antes estaban dispersos como "magic strings/numbers" en
  los adaptadores y la capa de API.
"""

from pydantic_settings import BaseSettings

# --- Endpoints de proveedores externos -------------------------------------
JINA_EMBEDDINGS_URL = "https://api.jina.ai/v1/embeddings"
JINA_EMBEDDING_TASK = "retrieval.query"
GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
# Ruta de búsqueda de Qdrant; se formatea con la colección y se cuelga del host.
QDRANT_SEARCH_PATH = "/collections/{collection}/points/search"

# --- Parámetros de red (antes hardcodeados en los adaptadores) -------------
JINA_TIMEOUT_SECONDS = 10
GROQ_TIMEOUT_SECONDS = 40
GROQ_MAX_RETRIES = 3
GROQ_RETRY_BASE_DELAY_SECONDS = 1.0

# --- Retrieval -------------------------------------------------------------
DEFAULT_TOP_K = 5

# --- Códigos de estado HTTP ------------------------------------------------
HTTP_TOO_MANY_REQUESTS = 429
HTTP_SERVICE_UNAVAILABLE = 503

# --- Validación de la petición ---------------------------------------------
QUESTION_MIN_LENGTH = 3
QUESTION_MAX_LENGTH = 500

# --- Metadatos y mensajes de la API ----------------------------------------
API_TITLE = "Parcerolegal API"
API_DESCRIPTION = "Colombian legal search engine powered by RAG"
API_VERSION = "0.1.0"
CORS_ALLOW_ORIGINS = ["*"]
SERVICE_TIMEOUT_MESSAGE = "El servicio tardó demasiado en responder. Por favor intenta de nuevo."


class Settings(BaseSettings):
    groq_api_key: str = ""
    qdrant_url: str = ""
    qdrant_api_key: str = ""
    jina_api_key: str = ""
    environment: str = "development"
    similarity_threshold: float = 0.40
    top_k: int = DEFAULT_TOP_K
    embedding_model: str = "jina-embeddings-v3"
    embedding_dimensions: int = 1024
    llm_model: str = "llama-3.3-70b-versatile"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 1024
    qdrant_collection: str = "parcerolegal"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    return Settings()
