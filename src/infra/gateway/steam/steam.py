import httpx

from src.infra.gateway.steam.constants import (
    APP_DETAILS_URL,
    STEAM_API_INTERFACE_STORE_SERVICE,
    STEAM_API_METHOD_GET_APP_LIST,
    STEAM_API_VERSION_V1,
)
from src.infra.gateway.steam.models.api.i_store_service.get_app_list.v1.istore_service_get_app_list_v1 import (
    IStoreServiceGetAppListV1RequestDTO,
    IStoreServiceGetAppListV1ResponseDTO,
)
from src.infra.gateway.steam.models.store.api.app_details.store_api_app_details import (
    AppDetailsResponseDTO,
    StoreApiAppDetailsRequestDTO,
)


class SteamApi:
    def __init__(self, client: httpx.Client, base_url_api: str, base_store_url: str) -> None:
        self.__client = client
        self.__base_api_url = base_url_api
        self.__base_store_url = base_store_url

    def istore_service_get_app_list_v1(
        self,
        request: IStoreServiceGetAppListV1RequestDTO,
    ) -> IStoreServiceGetAppListV1ResponseDTO:
        base_url = httpx.URL(self.__base_api_url)
        url_path = f"/{STEAM_API_INTERFACE_STORE_SERVICE}/{STEAM_API_METHOD_GET_APP_LIST}/{STEAM_API_VERSION_V1}/"
        with self.__client as client:
            response = client.get(
            url=base_url.join(url_path),
            params=request.model_dump(exclude_none=True),
        )
        
        response.raise_for_status()
        return IStoreServiceGetAppListV1ResponseDTO.model_validate(response.json())
    
    def store_api_app_details(self, request: StoreApiAppDetailsRequestDTO) -> AppDetailsResponseDTO:
        base_url = httpx.URL(self.__base_store_url)
        with self.__client as client:
            response = client.get(
            url=base_url.join(APP_DETAILS_URL),
            params=request.model_dump(exclude_none=True),
        )
        response.raise_for_status()
        return AppDetailsResponseDTO.model_validate(response.json())
            