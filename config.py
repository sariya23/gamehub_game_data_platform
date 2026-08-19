from pathlib import Path

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.types import Seconds


class Config(BaseSettings):
    model_config = SettingsConfigDict(
        extra="ignore",
        env_file_encoding="utf-8",
    )

    steam_api_web_key: SecretStr = Field(validation_alias="STEAM_API_WEB_KEY")
    steam_api_response_timeout_seconds: Seconds = Field(validation_alias="STEAM_API_RESPONSE_TIMEOUT_SECONDS")


def load_config(env_path: str | Path) -> Config:
    path = Path(env_path)
    if not path.is_file():
        raise FileNotFoundError(f"Config file does not exist: {path}")

    return Config(_env_file=path)  # type: ignore[call-arg]
