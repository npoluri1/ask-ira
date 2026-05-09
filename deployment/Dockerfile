# Stage 1: Build
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
# Install ALL free providers + OpenAI (your key)
# OpenRouter/DeepSeek/Together/Fireworks use langchain-openai (already core)
RUN pip install --no-cache-dir --prefix=/install \
    --index-url https://download.pytorch.org/whl/cpu \
    --extra-index-url https://pypi.org/simple \
    -e ".[groq,gemini,ollama,huggingface,mistral,mcp,eval]"

# Stage 2: Runtime
FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r askira && useradd -r -g askira askira

COPY --from=builder /install /usr/local
COPY . .

RUN mkdir -p /app/data/chroma_db /app/data/financial_news /app/data/sample_reports \
    && chown -R askira:askira /app/data

USER askira

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
