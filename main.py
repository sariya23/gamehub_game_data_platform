import argparse
import calendar
import json
import uuid
from datetime import UTC, date, datetime
from io import BytesIO

import psycopg
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
    for app_detail_line in app_detail_raw.splitlines():
        if not app_detail_line.strip():
            continue

        raw_model = RawSteamAppLine.model_validate_json(app_detail_line)
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

non_game_count = sum(app.type != "game" for app in silver_apps)
coming_soon_count = sum(
    app.type == "game" and app.coming_soon is True for app in silver_apps
)
gold_games_by_steam_id = {
    app.steam_appid: app
    for app in silver_apps
    if app.type == "game" and app.coming_soon is not True
}
gold_games = list(gold_games_by_steam_id.values())
duplicate_game_count = (
    len(silver_apps) - non_game_count - coming_soon_count - len(gold_games)
)

log.info(
    "silver apps prepared for gold",
    total=len(silver_apps),
    non_games_skipped=non_game_count,
    coming_soon_skipped=coming_soon_count,
    duplicate_games_skipped=duplicate_game_count,
    games=len(gold_games),
)

gold_batch_size = 500
gold_lock_id = 4_704_942_104
inserted_games_count = 0
updated_games_count = 0
processed_games_count = 0

database_connection = psycopg.connect(
    host=config.database.host,
    port=config.database.port,
    user=config.database.user,
    password=config.database.password.get_secret_value(),
    dbname=config.database.name,
    sslmode=config.database.ssl_mode,
    autocommit=True,
)

try:
    with database_connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_lock(%s)", (gold_lock_id,))
        cursor.execute("SELECT source_id FROM dim_source WHERE name = %s", ("Steam",))
        source_row = cursor.fetchone()
        if source_row is None:
            raise RuntimeError("Steam source is missing in dim_source")
        steam_source_id = source_row[0]

        cursor.execute(
            "SELECT rating_source_id FROM dim_rating_source WHERE name = %s",
            ("Metacritic",),
        )
        rating_source_row = cursor.fetchone()
        if rating_source_row is None:
            raise RuntimeError("Metacritic source is missing in dim_rating_source")
        metacritic_source_id = rating_source_row[0]

        cursor.execute(
            "SELECT name, platform_id FROM dim_platform WHERE name = ANY(%s)",
            (["Windows", "macOS", "Linux"],),
        )
        platform_ids = {row[0]: row[1] for row in cursor.fetchall()}
        missing_platforms = {"Windows", "macOS", "Linux"} - platform_ids.keys()
        if missing_platforms:
            raise RuntimeError(
                f"Platforms are missing in dim_platform: {sorted(missing_platforms)}"
            )

    for gold_batch_number, gold_batch_start in enumerate(
        range(0, len(gold_games), gold_batch_size),
        start=1,
    ):
        gold_batch = gold_games[gold_batch_start : gold_batch_start + gold_batch_size]

        try:
            with database_connection.transaction():  # noqa: SIM117
                with database_connection.cursor() as cursor:
                    external_ids = [str(app.steam_appid) for app in gold_batch]
                    cursor.execute(
                        """
                        SELECT external_id, game_id
                        FROM game_source
                        WHERE source_id = %s AND external_id = ANY(%s)
                        """,
                        (steam_source_id, external_ids),
                    )
                    game_ids = {row[0]: row[1] for row in cursor.fetchall()}
                    existing_external_ids = set(game_ids)

                    for external_id in external_ids:
                        if external_id not in game_ids:
                            game_ids[external_id] = uuid.uuid4()

                    batch_dates = {app.release_date for app in gold_batch}
                    batch_dates.add(pipeline_date)
                    date_rows = [
                        (
                            int(value.strftime("%Y%m%d")),
                            value,
                            value.day,
                            value.month,
                            calendar.month_name[value.month],
                            (value.month - 1) // 3 + 1,
                            value.year,
                            value.isoweekday(),
                        )
                        for value in batch_dates
                    ]
                    cursor.executemany(
                        """
                        INSERT INTO dim_date (
                            date_key, date, day, month, month_name, quarter, year,
                            day_of_week
                        )
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (date_key) DO NOTHING
                        """,
                        date_rows,
                    )

                    game_rows = [
                        (
                            game_ids[str(app.steam_appid)],
                            app.name,
                            app.short_description,
                            app.detailed_description,
                            int(app.release_date.strftime("%Y%m%d")),
                        )
                        for app in gold_batch
                    ]
                    cursor.executemany(
                        """
                        INSERT INTO dim_game (
                            game_id, name, short_description,
                            detailed_description, release_date_key
                        )
                        VALUES (%s, %s, %s, %s, %s)
                        ON CONFLICT (game_id) DO UPDATE SET
                            name = EXCLUDED.name,
                            short_description = EXCLUDED.short_description,
                            detailed_description = EXCLUDED.detailed_description,
                            release_date_key = EXCLUDED.release_date_key
                        """,
                        game_rows,
                    )

                    game_source_rows = [
                        (
                            game_ids[str(app.steam_appid)],
                            steam_source_id,
                            str(app.steam_appid),
                        )
                        for app in gold_batch
                    ]
                    cursor.executemany(
                        """
                        INSERT INTO game_source (game_id, source_id, external_id)
                        VALUES (%s, %s, %s)
                        ON CONFLICT (source_id, external_id) DO NOTHING
                        """,
                        game_source_rows,
                    )

                    developer_names = sorted(
                        {
                            developer.strip()
                            for app in gold_batch
                            for developer in app.developers or []
                            if developer.strip()
                        }
                    )
                    if developer_names:
                        cursor.executemany(
                            """
                            INSERT INTO dim_developer (name)
                            VALUES (%s)
                            ON CONFLICT (name) DO NOTHING
                            """,
                            [(name,) for name in developer_names],
                        )
                        cursor.execute(
                            """
                            SELECT name, developer_id
                            FROM dim_developer
                            WHERE name = ANY(%s)
                            """,
                            (developer_names,),
                        )
                        developer_ids = {row[0]: row[1] for row in cursor.fetchall()}
                        developer_bridge_rows = list(
                            {
                                (
                                    game_ids[str(app.steam_appid)],
                                    developer_ids[developer.strip()],
                                )
                                for app in gold_batch
                                for developer in app.developers or []
                                if developer.strip()
                            }
                        )
                        cursor.executemany(
                            """
                            INSERT INTO bridge_game_developer (
                                game_id, developer_id
                            )
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                            """,
                            developer_bridge_rows,
                        )

                    genre_names = sorted(
                        {
                            genre.description.strip()
                            for app in gold_batch
                            for genre in app.genres or []
                            if genre.description and genre.description.strip()
                        }
                    )
                    if genre_names:
                        cursor.executemany(
                            """
                            INSERT INTO dim_genre (name)
                            VALUES (%s)
                            ON CONFLICT (name) DO NOTHING
                            """,
                            [(name,) for name in genre_names],
                        )
                        cursor.execute(
                            "SELECT name, genre_id FROM dim_genre WHERE name = ANY(%s)",
                            (genre_names,),
                        )
                        genre_ids = {row[0]: row[1] for row in cursor.fetchall()}
                        genre_bridge_rows = list(
                            {
                                (
                                    game_ids[str(app.steam_appid)],
                                    genre_ids[genre.description.strip()],
                                )
                                for app in gold_batch
                                for genre in app.genres or []
                                if genre.description and genre.description.strip()
                            }
                        )
                        cursor.executemany(
                            """
                            INSERT INTO bridge_game_genre (game_id, genre_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                            """,
                            genre_bridge_rows,
                        )

                    category_names = sorted(
                        {
                            category.description.strip()
                            for app in gold_batch
                            for category in app.categories or []
                            if category.description and category.description.strip()
                        }
                    )
                    if category_names:
                        cursor.executemany(
                            """
                            INSERT INTO dim_category (name)
                            VALUES (%s)
                            ON CONFLICT (name) DO NOTHING
                            """,
                            [(name,) for name in category_names],
                        )
                        cursor.execute(
                            """
                            SELECT name, category_id
                            FROM dim_category
                            WHERE name = ANY(%s)
                            """,
                            (category_names,),
                        )
                        category_ids = {row[0]: row[1] for row in cursor.fetchall()}
                        category_bridge_rows = list(
                            {
                                (
                                    game_ids[str(app.steam_appid)],
                                    category_ids[category.description.strip()],
                                )
                                for app in gold_batch
                                for category in app.categories or []
                                if category.description and category.description.strip()
                            }
                        )
                        cursor.executemany(
                            """
                            INSERT INTO bridge_game_category (game_id, category_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                            """,
                            category_bridge_rows,
                        )

                    platform_bridge_rows = []
                    for app in gold_batch:
                        if app.platforms is None:
                            continue
                        game_id = game_ids[str(app.steam_appid)]
                        if app.platforms.windows is True:
                            platform_bridge_rows.append(
                                (game_id, platform_ids["Windows"])
                            )
                        if app.platforms.mac is True:
                            platform_bridge_rows.append(
                                (game_id, platform_ids["macOS"])
                            )
                        if app.platforms.linux is True:
                            platform_bridge_rows.append(
                                (game_id, platform_ids["Linux"])
                            )
                    if platform_bridge_rows:
                        cursor.executemany(
                            """
                            INSERT INTO bridge_game_platform (game_id, platform_id)
                            VALUES (%s, %s)
                            ON CONFLICT DO NOTHING
                            """,
                            platform_bridge_rows,
                        )

                    rating_rows = [
                        (
                            game_ids[str(app.steam_appid)],
                            metacritic_source_id,
                            int(pipeline_date.strftime("%Y%m%d")),
                            app.metacritic.score,
                            app.metacritic.url,
                        )
                        for app in gold_batch
                        if app.metacritic is not None
                        and (
                            app.metacritic.score is not None
                            or app.metacritic.url is not None
                        )
                    ]
                    if rating_rows:
                        cursor.executemany(
                            """
                            INSERT INTO fact_game_rating (
                                game_id, rating_source_id, snapshot_date_key,
                                score, url
                            )
                            VALUES (%s, %s, %s, %s, %s)
                            ON CONFLICT (
                                game_id, rating_source_id, snapshot_date_key
                            ) DO UPDATE SET
                                score = EXCLUDED.score,
                                url = EXCLUDED.url
                            """,
                            rating_rows,
                        )

                    screenshot_rows = [
                        (
                            game_ids[str(app.steam_appid)],
                            screenshot.path_thumbnail,
                            screenshot.path_full,
                            position,
                        )
                        for app in gold_batch
                        for position, screenshot in enumerate(
                            app.screenshots or [], start=1
                        )
                        if screenshot.path_full
                    ]
                    if screenshot_rows:
                        cursor.executemany(
                            """
                            INSERT INTO game_screenshot (
                                game_id, thumbnail_url, full_url, position
                            )
                            VALUES (%s, %s, %s, %s)
                            ON CONFLICT (game_id, position) DO UPDATE SET
                                thumbnail_url = EXCLUDED.thumbnail_url,
                                full_url = EXCLUDED.full_url
                            """,
                            screenshot_rows,
                        )

            batch_inserted_count = sum(
                external_id not in existing_external_ids for external_id in external_ids
            )
            inserted_games_count += batch_inserted_count
            updated_games_count += len(gold_batch) - batch_inserted_count
            processed_games_count += len(gold_batch)
            log.info(
                "gold batch saved",
                batch_number=gold_batch_number,
                batch_size=len(gold_batch),
                inserted_games=batch_inserted_count,
                updated_games=len(gold_batch) - batch_inserted_count,
            )
        except Exception:
            log.exception(
                "gold batch failed",
                batch_number=gold_batch_number,
                batch_size=len(gold_batch),
            )
            raise
finally:
    try:
        with database_connection.cursor() as cursor:
            cursor.execute("SELECT pg_advisory_unlock(%s)", (gold_lock_id,))
    finally:
        database_connection.close()

log.info(
    "gold load completed",
    processed_games=processed_games_count,
    inserted_games=inserted_games_count,
    updated_games=updated_games_count,
    pipeline_date=pipeline_date.isoformat(),
)
