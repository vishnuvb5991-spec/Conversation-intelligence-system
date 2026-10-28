from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    openai_api_key: str | None = None
    cohere_api_key: str | None = None
    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "enterprise_documents"
    embedding_model: str = "text-embedding-3-large"
    answer_model: str = "gpt-4.1-mini"
    chunk_size: int = 900
    chunk_overlap: int = 120
    dense_dimensions: int = 3072
    public_demo: bool = True
    auto_seed_demo: bool = True
    rate_limit_per_minute: int = 20
    openai_timeout_seconds: float = 12.0


settings = Settings()
