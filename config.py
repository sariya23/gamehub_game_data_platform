from pathlib import Path

from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

from src.types import Seconds


class SteamRateLimiterConfig(BaseModel):
    requests: int
    period_seconds: Seconds


class SteamAuthKeyConfig(BaseModel):
    steam_api_web_key: SecretStr


class SteamHTTPConfig(BaseModel):
    steam_api_response_timeout_seconds: Seconds


class SteamConfig(BaseModel):
    rate_limiter: SteamRateLimiterConfig
    auth: SteamAuthKeyConfig
    http: SteamHTTPConfig


class S3Config(BaseModel):
    admin_port: int
    api_port: int
    root_user: str
    root_password: SecretStr
    host: str
    secure: bool


class DatabaseConfig(BaseModel):
    driver: str
    host: str
    port: int
    user: str
    password: SecretStr
    name: str
    ssl_mode: str


class EnvConfig(BaseModel):
    type: str


class Config(BaseSettings):
    steam: SteamConfig
    s3: S3Config
    database: DatabaseConfig
    env: EnvConfig

    model_config = SettingsConfigDict(
        env_file=".env",
        env_nested_delimiter="__",
        case_sensitive=False,
    )


def load_config(env_path: str | Path) -> Config:
    path = Path(env_path)
    if not path.is_file():
        raise FileNotFoundError(f"Config file does not exist: {path}")

    return Config(_env_file=path)  # type: ignore[call-arg]
