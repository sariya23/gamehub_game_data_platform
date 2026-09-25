import argparse
import json
from datetime import UTC, date, datetime

import structlog

from config import load_config
from src.lib.datetime.datetime import parse_release_date_from_human
from src.models.steam.game import Game, Genre
from src.models.raw.models import RawBatch, RawSteamAppLine
from src.http.clients.steam import create_steam_api_http_client
from src.infra.gateway.steam.constants import STEAM_API_BASE_URL, STEAM_STORE_BASE_URL
from src.infra.gateway.steam.create import create_steam_api_client
from src.infra.gateway.steam.models.api.i_store_service.get_app_list.v1.istore_service_get_app_list_v1 import (
    IStoreServiceGetAppListV1RequestDTO,
)
from src.lib.rate_limit.create import create_rate_limiter
from src.lib.rate_limit.rate_limit import RateLimitConfig
from src.resources.steam.create import (
    create_steam_app_detail_resource,
    create_steam_app_list_resource,
)


def parse_pipeline_date(value: str) -> date:
    try:
        parsed_date = date.fromisoformat(value.replace("/", "-"))
    except ValueError as error:
        raise argparse.ArgumentTypeError(
            "date must be in YYYY/MM/DD format, for example 2026/08/27"
        ) from error

    if value != parsed_date.strftime("%Y/%m/%d"):
        raise argparse.ArgumentTypeError(
            "date must be in YYYY/MM/DD format, for example 2026/08/27"
        )

    return parsed_date


def get_pipeline_date() -> date:
    parser = argparse.ArgumentParser(
        description="Run the Steam data pipeline for an S3 partition date",
    )
    parser.add_argument(
        "--pipe_date",
        type=parse_pipeline_date,
        default=datetime.now(UTC).date(),
        metavar="YYYY/MM/DD",
        help="S3 partition date; defaults to the current UTC date",
    )
    return parser.parse_args().pipe_date

def iter_steam_games(app_detail_batches: list[RawBatch]):
    for batch in app_detail_batches:
        for game_record in batch.records:
            try:
                raw_game_line = RawSteamAppLine.model_validate(game_record)
                game_response = next(iter(raw_game_line.root.values()))
                if not game_response.success:
                    log.error(f"failed response to get game with id {raw_game_line.root.keys()}")
                    continue
                log.info(f"success validate resp for game {game_response.data.steam_appid} {game_response.data.name}")
                yield game_response.data
                    
            except Exception as e:
                log.error(f"got error while validate raw game line with {game_record.keys} error: {e} ")
                continue

pipeline_date = get_pipeline_date()


log = structlog.get_logger()
config = load_config(".env.local")
log.info(
    "pipeline started",
    environment=config.env.type,
    pipeline_date=pipeline_date.isoformat(),
)

steam_http_client = create_steam_api_http_client(config.steam)
steam_api = create_steam_api_client(
    steam_http_client, STEAM_STORE_BASE_URL, STEAM_API_BASE_URL
)
steam_list_resource = create_steam_app_list_resource(steam_api)
rate_limiter = create_rate_limiter(RateLimitConfig(1, 1))
steam_app_details_resource = create_steam_app_detail_resource(steam_api, rate_limiter)


app_batches = steam_list_resource._debug_get_game_batches(
    limit=10,
    request=IStoreServiceGetAppListV1RequestDTO(
        max_results=2,
        include_dlc=True,
        include_games=True,
        include_hardware=True,
        include_software=True,
        include_videos=True,
    ),
)

app_detail_batches = steam_app_details_resource.get_app_details(app_batches)
games_response = []

total_games = sum([len(r.records) for r in app_detail_batches])
log.info(f"total games {total_games}")

for game_resp in iter_steam_games(app_detail_batches):
    if game_resp.release_date and game_resp.release_date.coming_soon:
        continue
    try:
        game = Game(name=game_resp.name, steam_id=int(game_resp.steam_appid), 
                    description=game_resp.detailed_description, short_description=game_resp.short_description, 
                    header_image_url=game_resp.header_image, developers=game_resp.developers, 
                    metacritic_score=int(game_resp.metacritic.score), metacritic_url=game_resp.metacritic.url, 
                    genres=[Genre(name=i.description, steam_id=int(i.id)) for i in game_resp.genres], 
                    screenshots=[i.path_full for i in game_resp.screenshots], recommendations=int(game_resp.recommendations.total), 
                    release_date=parse_release_date_from_human(game_resp.release_date.date), 
                    available_on_windows=game_resp.platforms.windows, available_on_linux=game_resp.platforms.linux,
                    available_on_mac=game_resp.platforms.mac, steam_url=f"https://store.steampowered.com/app/{game_resp.steam_appid}")
        log.info(f"success validate resp for game {game_resp.steam_appid} {game_resp.name}")
    except Exception as e:
        log.error(f"got error while validate game with {game_resp.steam_appid} error: {e} ")
        continue
    