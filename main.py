import json
from io import BytesIO

import structlog

from config import load_config
from src.http.clients.steam import create_steam_api_http_client
from src.infra.gateway.steam.constants import STEAM_API_BASE_URL, STEAM_STORE_BASE_URL
from src.infra.gateway.steam.create import create_steam_api_client
from src.infra.s3.minio.create import create_minio
from src.lib.rate_limit.create import create_rate_limiter
from src.lib.rate_limit.rate_limit import RateLimitConfig
from src.resources.steam.create import (
    create_steam_app_detail_resource,
    create_steam_app_list_resource,
)
from src.models.silver.models import SilverSteamApp
from src.models.raw.models import RawSteamApp

log = structlog.get_logger()
config = load_config(".env.local")
log.info(f"start in '{config.env.type}' env")

m = create_minio(config=config.s3)
steam_http_client = create_steam_api_http_client(config.steam)
steam_api = create_steam_api_client(
    steam_http_client, STEAM_STORE_BASE_URL, STEAM_API_BASE_URL
)
steam_list_resource = create_steam_app_list_resource(steam_api)
rate_limiter = create_rate_limiter(RateLimitConfig(1, 1))
steam_app_details_resource = create_steam_app_detail_resource(steam_api, rate_limiter)

bucket_name = "gamehub"
m.create_or_ignore_bucket(bucket_name)


app_batches = steam_list_resource._debug_get_game_batches(5, 1)
for batch_number, batch in enumerate(app_batches, start=1):
    jsonl = "".join(
        json.dumps(record, ensure_ascii=False) + "\n" for record in batch.records
    )
    data = jsonl.encode("utf-8")
    object_key = m.build_object_key("raw",
        batch.source,
        object_group="app",
        load_date=batch.extracted_at,
        filename=f"batch_app_{batch_number:05d}.jsonl",
    )
    m.upload_file(BytesIO(data), object_key, len(data), bucket_name)

app_detail_batches = steam_app_details_resource.get_app_details(app_batches)
for batch_number, batch in enumerate(app_detail_batches, start=1):
    jsonl = "".join(
        json.dumps(record, ensure_ascii=False) + "\n" for record in batch.records
    )
    data = jsonl.encode("utf-8")
    object_key = m.build_object_key("raw",
        batch.source,
        object_group="app_detail",
        load_date=batch.extracted_at,
        filename=f"batch_app_details{batch_number:05d}.jsonl",
    )
    m.upload_file(BytesIO(data), object_key, len(data), bucket_name)


for app_detail_raw in m.get_files("gamehub", "raw/steam/app_detail/2026/8/21/"):
    raw_model = RawSteamApp.model_validate_json(app_detail_raw)
    log.info(raw_model)
    silver_model = SilverSteamApp.from_raw(raw_model)