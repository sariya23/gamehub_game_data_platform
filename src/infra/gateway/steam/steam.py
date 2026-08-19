import httpx

from src.infra.gateway.steam.constants import (
    STEAM_API_INTERFACE_STORE_SERVICE,
    STEAM_API_METHOD_GET_APP_LIST,
    STEAM_API_VERSION_V1,
)
from src.infra.gateway.steam.models.api.i_store_service.get_app_list.v1.istore_service_get_app_list_v1 import (
    IStoreServiceGetAppListV1RequestDTO,
)
from src.types import Seconds


class SteamApi:
    def __init__(self, timeout: Seconds, web_api_token: str, base_url_api: str, base_store_url: str) -> None:
        self.__client = httpx.Client(timeout=timeout, headers={"x-webapi-key": web_api_token})
        self.__base_api_url = base_url_api
        self.__base_store_url = base_store_url
        self.__token = web_api_token
    
    def isotre_service_get_app_list_v1(
        self,
        request: IStoreServiceGetAppListV1RequestDTO,
    ) -> dict[str, object]:
        base_url = httpx.URL(self.__base_api_url)
        url_path = f"/{STEAM_API_INTERFACE_STORE_SERVICE}/{STEAM_API_METHOD_GET_APP_LIST}/{STEAM_API_VERSION_V1}/"
        response = self.__client.get(
            url=base_url.join(url_path),
            params=request.model_dump(exclude_none=True),
        )
        response.raise_for_status()

        return response.json()