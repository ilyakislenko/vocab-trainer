from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="VOCAB_", env_file=".env")
    database_url: str = "sqlite+aiosqlite:///./vocab.db"
    llm_provider: Literal["api", "none"] = "none"
    llm_base_url: str = "http://localhost:11434/v1"
    llm_model: str = "llama3.1"
    llm_api_key: str | None = None
    llm_timeout: float = 60.0  # seconds; generous so a cold model load doesn't 502
