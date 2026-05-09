import sys

from src.config import get_settings

# All supported providers
ALL_PROVIDERS = {
    "openai", "groq", "gemini", "ollama", "huggingface",
    "openrouter", "deepseek", "mistral", "together", "fireworks",
    "replicate", "anthropic",
}

# Providers that need an API key
KEYED_PROVIDERS = {
    "openai": ("openai_api_key", "OPENAI_API_KEY"),
    "groq": ("groq_api_key", "GROQ_API_KEY"),
    "gemini": ("google_api_key", "GOOGLE_API_KEY"),
    "huggingface": ("huggingface_api_key", "HUGGINGFACE_API_KEY"),
    "openrouter": ("openrouter_api_key", "OPENROUTER_API_KEY"),
    "deepseek": ("deepseek_api_key", "DEEPSEEK_API_KEY"),
    "mistral": ("mistral_api_key", "MISTRAL_API_KEY"),
    "together": ("together_api_key", "TOGETHER_API_KEY"),
    "fireworks": ("fireworks_api_key", "FIREWORKS_API_KEY"),
    "replicate": ("replicate_api_key", "REPLICATE_API_KEY"),
    "anthropic": ("anthropic_api_key", "ANTHROPIC_API_KEY"),
}

# Providers that run locally (no API key needed)
LOCAL_PROVIDERS = {"ollama"}


def validate_config() -> None:
    settings = get_settings()

    warnings: list[str] = []
    errors: list[str] = []

    provider = (settings.llm_provider or "openai").lower()

    if provider in KEYED_PROVIDERS:
        attr, env_var = KEYED_PROVIDERS[provider]
        if not getattr(settings, attr, None):
            msg = f"{env_var} is required when llm_provider='{provider}'"
            if settings.environment == "production":
                errors.append(msg)
            else:
                warnings.append(msg)
                warnings.append(
                    f"  → Sign up for a free key: see .env.example for links"
                )
    elif provider in LOCAL_PROVIDERS:
        pass
    else:
        warnings.append(
            f"Unknown llm_provider '{provider}'. "
            f"Supported: {', '.join(sorted(ALL_PROVIDERS))}"
        )

    if not settings.chroma_persist_dir:
        errors.append("CHROMA_PERSIST_DIR is required")

    level = settings.log_level.upper()
    if level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
        warnings.append(f"Invalid LOG_LEVEL '{settings.log_level}', defaulting to INFO")

    if errors:
        print("Configuration ERRORS:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)

    if warnings:
        print("Configuration WARNINGS:")
        for w in warnings:
            print(f"  - {w}")
