from collections.abc import Iterator
from contextlib import AbstractContextManager
from datetime import UTC, datetime

import structlog

from src.infra.gateway.steam.steam import (
    IStoreServiceGetAppListV1RequestDTO,
    StoreApiAppDetailsRequestDTO,
)
from src.models.models import RawBatch
from src.resources.steam.interface import ISteamAppDetail, ISteamList

log = structlog.get_logger()

class SteamAppListResource:
    source_name = "steam"
    def __init__(self, steam_api: ISteamList):
        self.__steam_api = steam_api
        
    def iter_game_baches(self, batch_size: int) -> Iterator[RawBatch]:
        last_appid = None
        total = 0
        have_more_results = True

        while not have_more_results:
            response = self.__steam_api.istore_service_get_app_list_v1(
                IStoreServiceGetAppListV1RequestDTO(
                    last_appid=last_appid,
                    max_results=batch_size,
                )
            )

            apps = response.response.apps

            if not apps:
                break

            yield RawBatch(
                source=self.source_name,
                resource="app_list",
                records=[
                    app.model_dump(mode="json")
                    for app in apps
                ],
                extracted_at=datetime.now(UTC),
            )

            total += len(apps)
            log.debug(f"get {total} games")

            last_appid = response.response.last_appid
            have_more_results = response.response.have_more_results
    
    def _debug_iter_game_baches(self, limit: int, batch_size: int) -> Iterator[RawBatch]:
        last_appid = None
        total = 0

        while total < limit:
            current_batch_size = min(batch_size, limit - total)

            response = self.__steam_api.istore_service_get_app_list_v1(
                IStoreServiceGetAppListV1RequestDTO(
                    last_appid=last_appid,
                    max_results=current_batch_size,
                )
            )

            apps = response.response.apps

            if not apps:
                break

            yield RawBatch(
                source=self.source_name,
                resource="app_list",
                records=[
                    app.model_dump(mode="json")
                    for app in apps
                ],
                extracted_at=datetime.now(UTC),
            )

            total += len(apps)

            if not response.response.have_more_results:
                break

            last_appid = response.response.last_appid


    
class SteamAppDetailResource:
    source_name = "steam"
    
    def __init__(self, steam_api: ISteamAppDetail, rate_limiter: AbstractContextManager):
        self.__steam_api = steam_api
        self.__rate_limiter = rate_limiter
    
    def get_app_detail(self, app_batches: Iterator[RawBatch]) -> Iterator[RawBatch]:
        records = []

        for batch in app_batches:
            for app in batch.records:
                with self.__rate_limiter:
                    app_detail = self.__steam_api.store_api_app_details(
                        request=StoreApiAppDetailsRequestDTO(
                            appids=app["appid"],
                        )
                    )

                records.append(
                    app_detail.model_dump(mode="json")
                )
            yield RawBatch(
                source=self.source_name,
                resource="app_details",
                records=records,
                extracted_at=datetime.now(UTC),
            ) 

                
            
                
                
            
            