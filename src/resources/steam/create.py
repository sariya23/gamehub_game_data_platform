from contextlib import AbstractContextManager

from src.resources.steam.interface import ISteamAppDetail, ISteamList
from src.resources.steam.steam import SteamAppDetailResource, SteamAppListResource


def create_steam_app_list_resource(steam_api_client: ISteamList) -> SteamAppListResource:
    return SteamAppListResource(steam_api_client)


def create_steam_app_detail_resource(steam_api_client: ISteamAppDetail, rate_limiter: AbstractContextManager) -> SteamAppDetailResource:
    return SteamAppDetailResource(steam_api=steam_api_client, rate_limiter=rate_limiter)