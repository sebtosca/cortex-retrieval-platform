from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # LLM
    anthropic_api_key: str = ""
    rag_model: str = "claude-haiku-4-5-20251001"
    eval_model: str = "claude-sonnet-4-6"

    # Qdrant
    qdrant_url: str = "http://localhost:6333"
    qdrant_collection: str = "cortex_ai_initiatives"

    # PostgreSQL
    postgres_url: str = "postgresql+asyncpg://cortex:cortex@localhost:5432/cortex"

    # Redis
    redis_url: str = "redis://localhost:6379"

    # Financial data
    tracked_tickers: list[str] = ["AAPL", "MSFT", "GOOGL", "AMZN", "META", "NVDA", "IBM"]

    # Retrieval
    dense_top_k: int = 40
    rerank_top_k: int = 10
    chunk_size: int = 512
    chunk_overlap: int = 100

    # Observability
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "cortex-api"


settings = Settings()
