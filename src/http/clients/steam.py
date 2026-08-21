import httpx

from config import SteamConfig


def create_steam_api_http_client(config: SteamConfig) -> httpx.Client:
    return httpx.Client(timeout=config.http.steam_api_response_timeout_seconds, 
                        headers={"x-webapi-key": config.auth.steam_api_web_key.get_secret_value()})