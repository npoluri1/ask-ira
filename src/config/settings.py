from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # =========================================================================
    # LLM PROVIDER — Choose from ANY of the providers below
    # =========================================================================
    # Set LLM_PROVIDER in .env to switch. Default is "openai" (your key).
    #
    # PROVIDER            | COST      | SIGN UP
    # --------------------|-----------|--------------------------------------------------
    # openai              | Your key  | You already have a key
    # groq                | FREE      | https://console.groq.com (no credit card)
    # gemini              | FREE      | https://aistudio.google.com (60 req/min)
    # ollama              | FREE      | https://ollama.com (local, no API key)
    # huggingface         | FREE      | https://huggingface.co/settings/tokens
    # openrouter          | FREE      | https://openrouter.ai (free tier, 200+ models)
    # deepseek            | FREE~     | https://platform.deepseek.com ($0.14/m tokens)
    # mistral             | FREE      | https://console.mistral.ai (free tier)
    # together            | FREE      | https://together.ai ($25 free credits)
    # fireworks           | FREE      | https://fireworks.ai (free tier)
    # replicate           | FREE      | https://replicate.com (free trial credits)
    # anthropic           | PAID      | Paid key required
    # =========================================================================
    llm_provider: str = "openai"

    # --- OpenAI (your existing key) ---
    openai_api_key: str = ""

    # --- FREE PROVIDER API KEYS (set the one matching your LLM_PROVIDER) ---
    groq_api_key: str = ""             # Groq — https://console.groq.com
    google_api_key: str = ""           # Gemini — https://aistudio.google.com
    huggingface_api_key: str = ""      # HuggingFace — https://huggingface.co/settings/tokens
    openrouter_api_key: str = ""       # OpenRouter — https://openrouter.ai/keys
    deepseek_api_key: str = ""         # DeepSeek — https://platform.deepseek.com
    mistral_api_key: str = ""          # Mistral — https://console.mistral.ai
    together_api_key: str = ""         # Together AI — https://together.ai/api
    fireworks_api_key: str = ""        # Fireworks AI — https://fireworks.ai
    replicate_api_key: str = ""        # Replicate — https://replicate.com

    # --- PAID PROVIDER KEYS ---
    anthropic_api_key: str = ""

    # =========================================================================
    # OBSERVABILITY
    # =========================================================================
    langsmith_tracing: bool = False
    langsmith_endpoint: str = "https://api.smith.langchain.com"
    langsmith_api_key: str = ""
    langsmith_project: str = "ask-ira"

    # =========================================================================
    # DATABASE
    # =========================================================================
    postgres_dsn: str = ""

    # =========================================================================
    # APPLICATION
    # =========================================================================
    environment: str = "development"
    chroma_persist_dir: str = "./data/chroma"
    mcp_market_api_key: str = ""
    mcp_news_api_key: str = ""
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dimensions: int = 384
    embedding_top_k: int = 5
    log_level: str = "INFO"
    log_format: str = "json"

    # =========================================================================
    # CACHING
    # =========================================================================
    redis_url: str = ""
    redis_default_ttl: int = 300
    cache_enabled: bool = True
    cache_ttl_mcp: int = 300
    cache_ttl_rag: int = 600

    # =========================================================================
    # SECURITY
    # =========================================================================
    cors_origins: str = "*"
    rate_limit_max: int = 100
    rate_limit_window: int = 60
    enable_websocket: bool = True
    enable_human_review: bool = False

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
