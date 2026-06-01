from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "GitHub Profile AI Reviewer"
    app_version: str = "1.0.0"
    app_host: str = "0.0.0.0"
    app_port: int = 8000

    github_token: str = Field(default="", alias="GITHUB_TOKEN")
    github_api_url: str = "https://api.github.com/graphql"

    codebert_model: str = "microsoft/codebert-base"
    embedding_dim: int = 768
    request_timeout_seconds: float = 30.0

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore", populate_by_name=True)


settings = Settings()
