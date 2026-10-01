"""All app settings in one place, loaded and validated with Pydantic."""

import os
from urllib.parse import quote, urlunsplit

from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Load and check settings from `.env`.

    - `extra="ignore"` lets `.env` contain settings used by other parts (UI, evals)
      without causing an error.
    - If a required setting is missing, the app stops with a clear error.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- JINA AI (embeddings + reranker) ---
    JINA_API_KEY: str

    # --- OPENAI LLM ---
    OPENAI_API_KEY: str
    JUDGE_OPENAI_API_KEY: str | None = None

    # --- PORTKEY LLM GATEWAY ---
    PORTKEY_API_KEY: str
    PORTKEY_PRIMARY_SLUG: str = "openai-primary"
    PORTKEY_FALLBACK_SLUG: str = "anthropic-fallback"
    # ID (`pc-...`) of the saved Portkey config that holds the main and backup models.
    # Needed because this Portkey workspace only accepts saved configs.
    PORTKEY_PRIMARY_CONFIG_ID: str

    # --- QDRANT VECTOR DB ---
    QDRANT_URL: str = Field(validation_alias=AliasChoices("QDRANT_URL", "QDRANT_CLUSTER_ENDPOINT"))
    QDRANT_API_KEY: str | None = None
    QDRANT_COLLECTION: str = "enterprise_rag"

    # --- NEON SERVERLESS POSTGRES (LangGraph checkpointer) ---
    NEON_DB_URL: str

    # --- UPSTASH REDIS (rate limiting) ---
    UPSTASH_REDIS_REST_URL: str
    UPSTASH_REDIS_REST_TOKEN: str

    # --- API SAFETY ---
    API_KEY: str | None = Field(default=None, alias="RAG_API_KEY")
    RATE_LIMIT_PER_MINUTE: int = 20
    STRICT_STARTUP: bool = False

    # --- OBSERVABILITY ---
    LOGFIRE_TOKEN: str | None = None
    LOGFIRE_BASE_URL: str | None = None  # e.g. https://logfire-eu.pydantic.dev for EU tokens
    LANGSMITH_TRACING: str = "true"
    LANGSMITH_API_KEY: str | None = None
    LANGSMITH_PROJECT: str = "enterprise-agentic-rag"
    LANGSMITH_ENDPOINT: str = "https://api.smith.langchain.com"

    @field_validator("QDRANT_API_KEY", mode="before")
    @classmethod
    def _empty_qdrant_key_as_none(cls, v):
        """Treat an empty QDRANT_API_KEY as not set, so local Qdrant isn't sent a blank key."""
        if v == "" or v is None:
            return None
        return v

    @property
    def judge_api_key(self) -> str:
        """OpenAI key for the evaluation judge; uses the main key if no separate one is set."""
        return self.JUDGE_OPENAI_API_KEY or self.OPENAI_API_KEY

    @property
    def postgres_uri(self) -> str:
        """Postgres connection URL for the LangGraph checkpointer (Neon).

        Neon closes idle connections, so TCP keepalive options are added
        to keep connections alive between requests.
        """
        base = self.NEON_DB_URL.rstrip("/")
        keepalive = "keepalives=1&keepalives_idle=30&keepalives_interval=10&keepalives_count=5"
        if "?" in base:
            return f"{base}&{keepalive}"
        return f"{base}?{keepalive}"

    @property
    def redis_url(self) -> str:
        """Secure (TLS) Redis URL built from the Upstash REST settings.

        Upstash uses the same host for REST and Redis, and the REST token works
        as the Redis password. This URL is used for rate limiting and health checks.
        """
        host = self.UPSTASH_REDIS_REST_URL.replace("https://", "").rstrip("/")
        token = quote(self.UPSTASH_REDIS_REST_TOKEN, safe="")
        netloc = f"default:{token}@{host}"
        return urlunsplit(("rediss", netloc, "/0", "ssl_cert_reqs=required", ""))


# Singleton used across the app.
settings = Settings()


def apply_langchain_env():
    """Copy LangSmith settings into environment variables so tracing works automatically.

    Tracing is only turned on when both LANGSMITH_TRACING and LANGSMITH_API_KEY
    are set. Without a key, LangChain would log a 401 error on every agent step.
    """
    if settings.LANGSMITH_TRACING and settings.LANGSMITH_API_KEY:
        os.environ.setdefault("LANGCHAIN_TRACING_V2", settings.LANGSMITH_TRACING)
        os.environ.setdefault("LANGCHAIN_API_KEY", settings.LANGSMITH_API_KEY)
    if settings.LANGSMITH_PROJECT:
        os.environ.setdefault("LANGCHAIN_PROJECT", settings.LANGSMITH_PROJECT)
    if settings.LANGSMITH_ENDPOINT:
        os.environ.setdefault("LANGCHAIN_ENDPOINT", settings.LANGSMITH_ENDPOINT)


apply_langchain_env()
