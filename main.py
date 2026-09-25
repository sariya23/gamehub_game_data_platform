import argparse
from collections.abc import Iterator
from datetime import UTC, date, datetime

import structlog

from config import load_config
from src.http.clients.steam import create_steam_api_http_client
from src.infra.gateway.steam.constants import STEAM_API_BASE_URL, STEAM_STORE_BASE_URL
from src.infra.gateway.steam.create import create_steam_api_client
from src.infra.gateway.steam.models.api.i_store_service.get_app_list.v1.istore_service_get_app_list_v1 import (
    IStoreServiceGetAppListV1RequestDTO,
)
from src.lib.datetime.datetime import parse_release_date_from_human
from src.lib.logging.logging import configure_logging, register_secrets
from src.lib.rate_limit.create import create_rate_limiter
from src.lib.rate_limit.rate_limit import RateLimitConfig
from src.models.raw.models import RawBatch, RawSteamApp, RawSteamAppLine
from src.models.steam.game import Game, Genre
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

def iter_steam_games(app_detail_batches: list[RawBatch]) -> Iterator[RawSteamApp]:
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

pipeline_date = get_pipeline_date()


configure_logging()
log = structlog.get_logger(__name__)
config = load_config(".env.local")
register_secrets(
    config.steam.auth.steam_api_web_key.get_secret_value(),
    config.s3.root_password.get_secret_value(),
    config.database.password.get_secret_value(),
)
structlog.contextvars.bind_contextvars(pipeline_date=pipeline_date.isoformat())
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
log.info("games.fetched", total_games=total_games)

for game_resp in iter_steam_games(app_detail_batches):
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
    except Exception as e:
        log.exception("game.domain_failed", operation="domain_game", app_id=game_resp.steam_appid, game_name=game_resp.name, error_type=type(e).__name__)
        continue
    