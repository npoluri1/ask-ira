from langchain_core.language_models.chat_models import BaseChatModel

from src.config import get_settings

settings = get_settings()

# =============================================================================
# LLM Factory — Supports 13 providers (9 free, 2 paid)
# =============================================================================
# Set LLM_PROVIDER in .env to switch between providers.
#
# Free providers (no credit card needed):
#   groq, gemini, ollama, huggingface, openrouter, deepseek, mistral, together, fireworks
#
# Paid providers:
#   openai (you have key), anthropic, replicate
# =============================================================================


def get_llm(
    provider: str | None = None,
    model: str | None = None,
    temperature: float = 0.0,
    streaming: bool = True,
) -> BaseChatModel:
    provider = provider or settings.llm_provider or "openai"

    # --- OpenAI (your key) ---
    if provider == "openai":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model or "gpt-4o",
            temperature=temperature,
            streaming=streaming,
            api_key=settings.openai_api_key,
        )

    # --- Groq (FREE — Llama 3, Mixtral, Gemma 2 — 30 req/min) ---
    # Sign up: https://console.groq.com
    if provider == "groq":
        from langchain_groq import ChatGroq

        return ChatGroq(
            model=model or "llama3-70b-8192",
            temperature=temperature,
            streaming=streaming,
            api_key=settings.groq_api_key or None,
        )

    # --- Gemini (FREE — Gemini 1.5 Flash/Pro — 60 req/min) ---
    # Sign up: https://aistudio.google.com
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI

        return ChatGoogleGenerativeAI(
            model=model or "gemini-1.5-flash",
            temperature=temperature,
            streaming=streaming,
            google_api_key=settings.google_api_key,
        )

    # --- Ollama (FREE — local models, no API key needed) ---
    # Install: https://ollama.com → run: ollama pull llama3.2
    if provider == "ollama":
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model or "llama3.2",
            temperature=temperature,
            num_predict=4096,
        )

    # --- HuggingFace (FREE — HF inference endpoints) ---
    # Sign up: https://huggingface.co/settings/tokens
    if provider == "huggingface":
        from langchain_community.chat_models import ChatHuggingFace
        from langchain_huggingface import HuggingFaceEndpoint

        endpoint = HuggingFaceEndpoint(
            repo_id=model or "HuggingFaceH4/zephyr-7b-beta",
            task="text-generation",
            huggingfacehub_api_token=settings.huggingface_api_key or None,
        )
        return ChatHuggingFace(llm=endpoint, temperature=temperature)

    # --- OpenRouter (FREE — 200+ models via one API) ---
    # Sign up: https://openrouter.ai → Keys: https://openrouter.ai/keys
    # Free models: mistralai/mixtral-8x22b, meta-llama/llama-3-70b, google/gemma-2-27b
    if provider == "openrouter":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model or "mistralai/mixtral-8x22b-instruct",
            temperature=temperature,
            streaming=streaming,
            openai_api_key=settings.openrouter_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            default_headers={
                "HTTP-Referer": "https://github.com/your-org/ask-ira",
                "X-Title": "Ask IRA",
            },
        )

    # --- DeepSeek (FREE~ — $0.14/M tokens, $0.28/M output) ---
    # Sign up: https://platform.deepseek.com → API keys
    if provider == "deepseek":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model or "deepseek-chat",
            temperature=temperature,
            streaming=streaming,
            openai_api_key=settings.deepseek_api_key,
            openai_api_base="https://api.deepseek.com/v1",
        )

    # --- Mistral AI (FREE — Mistral Small/Medium/Large, 500k tokens free) ---
    # Sign up: https://console.mistral.ai
    if provider == "mistral":
        from langchain_mistralai import ChatMistralAI

        return ChatMistralAI(
            model=model or "mistral-small-latest",
            temperature=temperature,
            streaming=streaming,
            api_key=settings.mistral_api_key,
        )

    # --- Together AI (FREE — $25 free credits for new users) ---
    # Sign up: https://together.ai → API keys
    # Models: meta-llama/Llama-3-70b, mistralai/Mixtral-8x22b
    if provider == "together":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model or "meta-llama/Llama-3-70b-chat-hf",
            temperature=temperature,
            streaming=streaming,
            openai_api_key=settings.together_api_key,
            openai_api_base="https://api.together.xyz/v1",
        )

    # --- Fireworks AI (FREE — fast Llama 3, Mixtral, Qwen) ---
    # Sign up: https://fireworks.ai → API keys
    if provider == "fireworks":
        from langchain_openai import ChatOpenAI

        return ChatOpenAI(
            model=model or "accounts/fireworks/models/llama-v3-70b-instruct",
            temperature=temperature,
            streaming=streaming,
            openai_api_key=settings.fireworks_api_key,
            openai_api_base="https://api.fireworks.ai/inference/v1",
        )

    # --- Replicate (FREE trial credits — then pay-as-you-go) ---
    # Sign up: https://replicate.com → API tokens
    # Models: meta/meta-llama-3-70b-instruct, mistralai/mixtral-8x7b-instruct
    if provider == "replicate":
        from langchain_community.llms import Replicate

        llm = Replicate(
            model=model or "meta/meta-llama-3-70b-instruct",
            temperature=temperature,
            replicate_api_token=settings.replicate_api_key,
        )
        return llm

    # --- Anthropic (PAID — Claude Sonnet 4) ---
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic

        return ChatAnthropic(
            model=model or "claude-sonnet-4-20250514",
            temperature=temperature,
            streaming=streaming,
            api_key=settings.anthropic_api_key,
        )

    msg = (
        f"Unknown LLM provider '{provider}'. Choose: "
        f"openai, groq, gemini, ollama, huggingface, openrouter, "
        f"deepseek, mistral, together, fireworks, replicate, anthropic"
    )
    raise ValueError(msg)
