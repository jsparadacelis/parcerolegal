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
QDRANT_COLLECTION_PATH = "/collections/{collection}"
# Listar modelos no consume tokens; sirve para detectar un modelo retirado.
GROQ_MODELS_URL = "https://api.groq.com/openai/v1/models"

# --- Health check profundo ---------------------------------------------------
HEALTH_CHECK_TIMEOUT_SECONDS = 5
# Evita que llamadas repetidas a /api/health/deep multipliquen el tráfico
# (y el costo de Jina) hacia las dependencias externas.
HEALTH_CHECK_CACHE_TTL_SECONDS = 30.0

# --- Parámetros de red (antes hardcodeados en los adaptadores) -------------
JINA_TIMEOUT_SECONDS = 10
GROQ_TIMEOUT_SECONDS = 40
# Reintentos ante 429 (y 5xx transitorios en Jina). MAX_RETRIES es el total de
# intentos. MAX_RETRY_WAIT_SECONDS acota la espera acumulada por llamada para
# que embed + generate respondan antes del timeout de 45s del frontend
# (no hay timeout global en el backend): Jina <= 4s + Groq <= 12s de espera.
# Si el Retry-After del proveedor no cabe en ese presupuesto, se responde 503
# de inmediato en vez de esperar en vano.
GROQ_MAX_RETRIES = 3
GROQ_RETRY_BASE_DELAY_SECONDS = 1.0
GROQ_MAX_RETRY_WAIT_SECONDS = 12.0
JINA_MAX_RETRIES = 3
JINA_RETRY_BASE_DELAY_SECONDS = 0.5
JINA_MAX_RETRY_WAIT_SECONDS = 4.0
# gpt-oss es modelo de razonamiento: el razonamiento consume el mismo
# max_tokens que la respuesta. "low" deja margen a la respuesta y
# include_reasoning=False evita recibir el razonamiento en el payload.
GROQ_REASONING_EFFORT = "low"
GROQ_INCLUDE_REASONING = False

# --- Retrieval -------------------------------------------------------------
DEFAULT_TOP_K = 5

# --- Compartir ---------------------------------------------------------------
# nbytes para secrets.token_urlsafe → ~11 caracteres, 64 bits de entropía,
# suficiente para que un share_id no sea adivinable/enumerable.
SHARE_ID_BYTES = 8

# --- Códigos de estado HTTP ------------------------------------------------
HTTP_TOO_MANY_REQUESTS = 429
HTTP_SERVICE_UNAVAILABLE = 503
HTTP_TRANSIENT_SERVER_ERRORS = frozenset({500, 502, 503, 504})

# --- Validación de la petición ---------------------------------------------
QUESTION_MIN_LENGTH = 3
QUESTION_MAX_LENGTH = 500

# --- Metadatos y mensajes de la API ----------------------------------------
API_TITLE = "Parcerolegal API"
API_DESCRIPTION = "Colombian legal search engine powered by RAG"
API_VERSION = "0.1.0"
CORS_ALLOW_ORIGINS = ["*"]
SERVICE_TIMEOUT_MESSAGE = "El servicio tardó demasiado en responder. Por favor intenta de nuevo."
SERVICE_BUSY_MESSAGE = "Estamos recibiendo muchas consultas en este momento. Intenta de nuevo en unos segundos."
SERVICE_UNAVAILABLE_MESSAGE = "El servicio no está disponible en este momento. Por favor intenta de nuevo más tarde."
# Retry-After sugerido al cliente cuando el proveedor no envía uno propio.
SERVICE_BUSY_RETRY_AFTER_SECONDS = 10


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
    llm_model: str = "openai/gpt-oss-120b"
    llm_temperature: float = 0.0
    llm_max_tokens: int = 1024
    qdrant_collection: str = "parcerolegal"
    supabase_url: str = ""
    supabase_key: str = ""
    supabase_queries_table: str = "queries"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


def get_settings() -> Settings:
    return Settings()
