from collections.abc import Iterator

from src.infra.gateway.steam.steam import IStoreServiceGetAppListV1RequestDTO, SteamApi, StoreApiAppDetailsRequestDTO, AppDetailsResponseDTO
from src.infra.gateway.steam.models.api.i_store_service.get_app_list.v1.istore_service_get_app_list_v1 import IStoreServiceGetAppListV1ResponseSteamApp
from src.lib.rate_limit.rate_limit import RateLimiter

class SteamAppListResource:
    def __init__(self, steam_api: SteamApi):
        self.__steam_api = steam_api
        
    def iter_game_baches(self, limit: int, batch_size: int) -> Iterator[list[IStoreServiceGetAppListV1ResponseSteamApp]]:
        last_appid = None
        total = 0
        while True:
            response = self.__steam_api.istore_service_get_app_list_v1(
                IStoreServiceGetAppListV1RequestDTO(last_appid=last_appid, max_results=batch_size))
            
            yield response.response.apps

            total += len(response.response.apps)
            
            if batch_size >= limit or total >= limit or (not response.response.have_more_results):
                break

            last_appid = response.response.last_appid

    
class SteamAppDetailResource:
    def __init__(self, steam_api: SteamApi, rate_limiter: RateLimiter):
        self.__steam_api = steam_api
        self.__rate_limiter = rate_limiter
    
    def get_app_detail(self, app_batches: Iterator[list[IStoreServiceGetAppListV1ResponseSteamApp]]) -> Iterator[AppDetailsResponseDTO]:
        for batch in app_batches:
            for app in batch:
                with self.__rate_limiter:
                    app_detail = self.__steam_api.store_api_app_details(request=StoreApiAppDetailsRequestDTO(appids=app.appid))
                    yield app_detail
                
            
                
                
            
            