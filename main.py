import argparse
import json
from datetime import UTC, date, datetime
from io import BytesIO

import pyarrow as pa
import pyarrow.parquet as pq
import structlog

from config import load_config
from src.http.clients.steam import create_steam_api_http_client
from src.infra.gateway.steam.constants import STEAM_API_BASE_URL, STEAM_STORE_BASE_URL
from src.infra.gateway.steam.create import create_steam_api_client
from src.infra.gateway.steam.models.api.i_store_service.get_app_list.v1.istore_service_get_app_list_v1 import (
    IStoreServiceGetAppListV1RequestDTO,
)
from src.infra.s3.minio.create import create_minio
from src.infra.s3.minio.minio import Minio
from src.lib.rate_limit.create import create_rate_limiter
from src.lib.rate_limit.rate_limit import RateLimitConfig
from src.models.raw.models import RawSteamAppLine
from src.models.silver.exceptions import SilverRequiredFiledException
from src.models.silver.models import SilverSteamApp
from src.models.silver.shema import SILVER_APP_DEATAIL_SCHEMA
from src.resources.steam.create import (
    create_steam_app_detail_resource,
    create_steam_app_list_resource,
)


def load_silver_apps(
    minio: Minio,
    bucket_name: str,
    load_date: date,
) -> list[SilverSteamApp]:
    """Load Silver Parquet files from S3 and convert rows to models."""
    prefix = (
        f"silver/steam/app_detail/{load_date.year}/{load_date.month}/{load_date.day}/"
    )
    silver_apps: list[SilverSteamApp] = []

    for parquet_data in minio.get_files(bucket_name, prefix):
        table = pq.read_table(BytesIO(parquet_data))
        silver_apps.extend(
            SilverSteamApp.model_validate(row) for row in table.to_pylist()
        )

    return silver_apps


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


pipeline_date = get_pipeline_date()


log = structlog.get_logger()
config = load_config(".env.local")
log.info(
    "pipeline started",
    environment=config.env.type,
    pipeline_date=pipeline_date.isoformat(),
)

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


app_batches = steam_list_resource._debug_get_game_batches(
    limit=20,
    request=IStoreServiceGetAppListV1RequestDTO(
        max_results=2,
        include_dlc=True,
        include_games=True,
        include_hardware=True,
        include_software=True,
        include_videos=True,
    ),
)
for batch_number, batch in enumerate(app_batches, start=1):
    jsonl = "".join(
        json.dumps(record, ensure_ascii=False) + "\n" for record in batch.records
    )
    data = jsonl.encode("utf-8")
    object_key = m.build_object_key(
        "raw",
        batch.source,
        object_group="app",
        load_date=pipeline_date,
        filename=f"batch_app_{batch_number:05d}.jsonl",
    )
    m.upload_file(BytesIO(data), object_key, len(data), bucket_name)

app_detail_batches = steam_app_details_resource.get_app_details(app_batches)
for batch_number, batch in enumerate(app_detail_batches, start=1):
    jsonl = "".join(
        json.dumps(record, ensure_ascii=False) + "\n" for record in batch.records
    )
    data = jsonl.encode("utf-8")
    object_key = m.build_object_key(
        "raw",
        batch.source,
        object_group="app_detail",
        load_date=pipeline_date,
        filename=f"batch_app_details{batch_number:05d}.jsonl",
    )
    m.upload_file(BytesIO(data), object_key, len(data), bucket_name)

batch = []

raw_app_detail_prefix = (
    "raw/steam/app_detail/"
    f"{pipeline_date.year}/{pipeline_date.month}/{pipeline_date.day}/"
)
for app_detail_raw in m.get_files(bucket_name, raw_app_detail_prefix):
    raw_model = RawSteamAppLine.model_validate_json(app_detail_raw)
    for response in raw_model.root.values():
        if response.success is not True:
            continue

        if response.data is None:
            continue

        raw_app = response.data
        silver_model = None
        try:
            silver_model = SilverSteamApp.from_raw(raw_app)
        except SilverRequiredFiledException as e:
            log.warning(
                f"cannot transform silver model from raw. Exception: {e}, app id: {raw_app.steam_appid}"
            )
            continue

        batch.append(silver_model)

table = pa.Table.from_pylist(
    [app.model_dump(mode="python") for app in batch],
    schema=SILVER_APP_DEATAIL_SCHEMA,
)

buffer = pa.BufferOutputStream()
pq.write_table(
    table,
    buffer,
    compression="zstd",
)

parquet_bytes = buffer.getvalue().to_pybytes()

m.upload_file(
    bucket_name="gamehub",
    object_name=m.build_object_key(
        prefix="silver",
        source_name="steam",
        object_group="app_detail",
        load_date=pipeline_date,
        filename="silver_app_details_00001.parquet",
    ),
    data=BytesIO(parquet_bytes),
    l=len(parquet_bytes),
)

silver_apps = load_silver_apps(m, bucket_name, pipeline_date)
log.info(
    "silver apps loaded",
    count=len(silver_apps),
    pipeline_date=pipeline_date.isoformat(),
)
