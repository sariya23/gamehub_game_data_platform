from config import Config
from src.http.clients.steam import create_steam_api_http_client
from src.infra.database.postgres.postgres import PostgresClient
from src.infra.gateway.steam.constants import STEAM_API_BASE_URL, STEAM_STORE_BASE_URL
from src.infra.gateway.steam.create import create_steam_api_client
from src.lib.rate_limit.create import create_rate_limiter
from src.lib.rate_limit.rate_limit import RateLimitConfig
from src.resources.steam.create import (
    create_steam_app_detail_resource,
    create_steam_app_list_resource,
)


class App:
    def __init__(self, app_config: Config, rate_limit_config: RateLimitConfig):
        self.__app_config = app_config
        self.__rate_limit_config = rate_limit_config
        self.__steam_http_client = create_steam_api_http_client(self.__app_config.steam)
        self.__steam_api = create_steam_api_client(
            self.__steam_http_client, STEAM_STORE_BASE_URL, STEAM_API_BASE_URL
        )
        self.steam_list_resource = create_steam_app_list_resource(self.__steam_api)
        self.__rate_limiter = create_rate_limiter(self.__rate_limit_config)
        self.steam_app_details_resource = create_steam_app_detail_resource(self.__steam_api, self.__rate_limiter)
        self.postgres = PostgresClient(self.__app_config)
    
    