from collections.abc import Iterator
from typing import override

import structlog

from src.infra.gateway.steam.models.api.i_store_service.get_app_list.v1.istore_service_get_app_list_v1 import (
    IStoreServiceGetAppListV1RequestDTO,
)
from src.lib.datetime.datetime import parse_release_date_from_human
from src.models.raw.models import RawBatch, RawSteamApp, RawSteamAppLine
from src.models.steam.game import Game, Genre
from src.resources.steam.steam import SteamAppDetailResource, SteamAppListResource

log = structlog.get_logger(__name__)

class SteamAppPipeline:
    def __init__(self, steam_games_list_client: SteamAppListResource, steam_games_details_client: SteamAppDetailResource):
        self.__total_games = 0
        self.__fetched_games = 0
        self.__parsed_games = 0
        self.__saved_games = 0
        self._steam_games_list_client = steam_games_list_client
        self._steam_games_details_client = steam_games_details_client
    
    @property
    def total_games(self) -> int:
        return self.__total_games

    @property
    def fethced_games(self) -> int:
        return self.__fetched_games
    
    @property
    def parsed_games(self) -> int:
        return self.__parsed_games

    @property
    def saved_games(self) -> int:
        return self.__saved_games
    
    def get_list_apps(self, request: IStoreServiceGetAppListV1RequestDTO, limit: int) -> list[RawBatch]:
        app_batches = self._steam_games_list_client.get_all_games_batches(
            request=request
        )
        return app_batches
    
    def get_list_apps_details(self, raw_batches: list[RawBatch]) -> list[RawBatch]:
        return self._steam_games_details_client.get_app_details(raw_batches)
    
    def iter_raw_games(self, app_detail_batches: list[RawBatch]) -> Iterator[RawSteamApp]:
        for batch in app_detail_batches:
            for game_record in batch.records:
                try:
                    raw_game_line = RawSteamAppLine.model_validate(game_record)
                    game_response = next(iter(raw_game_line.root.values()))
                    if not game_response.success:
                        log.error("steam.app_unsuccessful", operation="validate_raw_game", app_ids=list(raw_game_line.root), reason="Steam returned success=false")
                        continue
                    log.info("game.raw_validated", app_id=game_response.data.steam_appid, game_name=game_response.data.name)
                    yield game_response.data
                        
                except Exception as e:
                    log.exception("game.raw_validation_failed", operation="validate_raw_game", app_ids=list(game_record), error_type=type(e).__name__)
                    continue        
    
    def iter_to_domain_games(self, raw_games: Iterator[RawSteamApp]) -> Iterator[Game]:
        for game_resp in raw_games:
            if game_resp.release_date and game_resp.release_date.coming_soon:
                log.info("game.skipped", app_id=game_resp.steam_appid, reason="unreleased")
                continue
            try:
                game = Game(name=game_resp.name, steam_id=game_resp.steam_appid, 
                            header_image_url=game_resp.header_image,
                            description=game_resp.detailed_description, short_description=(game_resp.short_description or game_resp.about_the_game),
                            genres=[Genre(name=i.description, steam_id=int(i.id or 0)) for i in game_resp.genres] if game_resp.genres else [], 
                            screenshots=[(i.path_full or "") for i in game_resp.screenshots] if game_resp.screenshots else [],
                            recommendations=int((game_resp.recommendations.total or 0) if game_resp.recommendations else 0), 
                            developers=game_resp.developers if game_resp.developers else [],
                            steam_url=f"https://store.steampowered.com/app/{game_resp.steam_appid}")
                if m := game_resp.metacritic:
                    game.metacritic_score = m.score
                    game.metacritic_url = m.url
                if d := game_resp.release_date:
                    game.release_date = parse_release_date_from_human(d.date) if d.date else None
                if p := game_resp.platforms:
                    game.available_on_linux = p.linux
                    game.available_on_mac = p.mac  
                    game.available_on_windows = p.windows
                log.info("game.domain", app_id=game_resp.steam_appid, game_name=game_resp.name)
                yield game
            except Exception as e:
                log.exception("game.domain_failed", operation="domain_game", app_id=game_resp.steam_appid, game_name=game_resp.name, error_type=type(e).__name__)
                continue
            
        
class SteamAppPipelineDebug(SteamAppPipeline):
    @override
    def get_list_apps(self, request: IStoreServiceGetAppListV1RequestDTO, limit: int) -> list[RawBatch]:
        app_batches = self._steam_games_list_client._debug_get_game_batches(
            limit=limit,
            request=request
            )
        return app_batches
    