
from typing import Protocol

from src.infra.gateway.steam.models.api.i_store_service.get_app_list.v1.istore_service_get_app_list_v1 import (
    IStoreServiceGetAppListV1ResponseDTO,
)
from src.infra.gateway.steam.models.store.api.app_details.store_api_app_details import (
    AppDetailsResponseDTO,
)
from src.infra.gateway.steam.steam import (
    IStoreServiceGetAppListV1RequestDTO,
    StoreApiAppDetailsRequestDTO,
)


class ISteamList(Protocol):
    def istore_service_get_app_list_v1(
        self, request: IStoreServiceGetAppListV1RequestDTO, ) -> IStoreServiceGetAppListV1ResponseDTO:
        ...


class ISteamAppDetail(Protocol):
    def store_api_app_details(self, request: StoreApiAppDetailsRequestDTO) -> AppDetailsResponseDTO:
        ...
    