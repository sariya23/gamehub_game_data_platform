from httpx import Client

from src.infra.gateway.steam.steam import SteamApi


def create_steam_api_client(client: Client, base_store_url: str, base_url_api: str) -> SteamApi:
    return SteamApi(client=client, base_store_url=base_store_url, base_url_api=base_url_api)