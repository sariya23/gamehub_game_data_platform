import httpx

from src.infra.gateway.steam.constants import (
    STEAM_API_INTERFACE_STORE_SERVICE,
    STEAM_API_METHOD_GET_APP_LIST,
    STEAM_API_VERSION_V1,
)
from src.infra.gateway.steam.models.istore_service_get_app_list_v1 import (
    IStoreServiceGetAppListV1RequestDTO,
    IStoreServiceGetAppListV1ResponseDTO,
)
from src.types import Seconds


class SteamApi:
    def __init__(self, timeout: Seconds, web_api_token: str, base_url: str) -> None:
        self.__client = httpx.Client(timeout=timeout, base_url=base_url, headers={"x-webapi-key": web_api_token})
        self.__token = web_api_token
    
    def isotre_service_get_app_list_v1(
        self,
        request: IStoreServiceGetAppListV1RequestDTO,
    ) -> IStoreServiceGetAppListV1ResponseDTO:
        url_path = f"/{STEAM_API_INTERFACE_STORE_SERVICE}/{STEAM_API_METHOD_GET_APP_LIST}/{STEAM_API_VERSION_V1}/"
        response = self.__client.get(
            url=url_path,
            params=request.model_dump(exclude_none=True),
        )
        response.raise_for_status()

        return IStoreServiceGetAppListV1ResponseDTO.model_validate_json(response.content)
