import argparse
from datetime import UTC, date, datetime

import structlog

from config import load_config
from src.lib.input.input import get_pipeline_date
from src.http.clients.steam import create_steam_api_http_client
from src.infra.gateway.steam.constants import STEAM_API_BASE_URL, STEAM_STORE_BASE_URL
from src.infra.gateway.steam.create import create_steam_api_client
from src.infra.gateway.steam.models.api.i_store_service.get_app_list.v1.istore_service_get_app_list_v1 import (
    IStoreServiceGetAppListV1RequestDTO,
)
from src.lib.logging.logging import configure_logging, register_secrets
from src.lib.rate_limit.create import create_rate_limiter
from src.lib.rate_limit.rate_limit import RateLimitConfig
from src.pipeline.steam import SteamAppPipelineDebug
from src.resources.steam.create import (
    create_steam_app_detail_resource,
    create_steam_app_list_resource,
)

log = structlog.get_logger(__name__)
configure_logging()

pipeline_date = get_pipeline_date()

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

pipeline = SteamAppPipelineDebug(steam_list_resource, steam_app_details_resource)

app_list = pipeline.get_list_apps(IStoreServiceGetAppListV1RequestDTO(), limit=10)
app_details = pipeline.get_list_apps_details(app_list)


for game in pipeline.iter_to_domain_games(pipeline.iter_raw_games(app_details)):
    print(game)
    