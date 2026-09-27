from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from time import perf_counter

import structlog

from config import load_config
from src.app.app import App
from src.infra.gateway.steam.models.api.i_store_service.get_app_list.v1.istore_service_get_app_list_v1 import (
    IStoreServiceGetAppListV1RequestDTO,
)
from src.lib.batched import batched
from src.lib.http import download_image
from src.lib.image import IMAGE_EXTENSIONS, get_image_mime
from src.lib.input.input import get_pipeline_date
from src.lib.logging.logging import configure_logging, register_secrets
from src.lib.rate_limit.rate_limit import RateLimitConfig
from src.models.dto.game_image import GameImageDTO
from src.pipeline.steam import SteamAppPipeline

log = structlog.get_logger(__name__)
configure_logging()

BATCH_SIZE = 1000
APP_LIMIT = 10
UPLOAD_WORKERS = 8
IMAGE_BUCKET = "game-catalog"


def elapsed(started_at):
    return round(perf_counter() - started_at, 3)


def main():
    started_at = perf_counter()
    stats = {
        "batches_processed": 0,
        "games_inserted": 0,
        "games_existing": 0,
        "games_processed": 0,
        "games_images_skipped": 0,
        "images_downloaded": 0,
        "downloaded_bytes": 0,
        "download_errors": 0,
        "images_uploaded": 0,
        "uploaded_bytes": 0,
        "upload_errors": 0,
        "image_records_saved": 0,
    }
    status = "failed"

    def fetch_image(url, image_log):
        download_started_at = perf_counter()
        image_log.info("image.download_started", source_url=url, destination="memory")
        try:
            data = download_image(url)
        except Exception:
            stats["download_errors"] += 1
            image_log.exception(
                "image.download_failed",
                source_url=url,
                duration_seconds=elapsed(download_started_at),
            )
            raise
        stats["images_downloaded"] += 1
        stats["downloaded_bytes"] += len(data)
        image_log.info(
            "image.download_completed",
            source_url=url,
            destination="memory",
            size_bytes=len(data),
            duration_seconds=elapsed(download_started_at),
        )
        return data

    def upload_image(data, dto, image_log):
        upload_started_at = perf_counter()
        image_log = image_log.bind(
            source_url=dto.source_url,
            bucket=dto.bucket,
            object_key=dto.object_key,
            size_bytes=len(data),
        )
        image_log.info("image.upload_started")
        try:
            app.minio.upload_file(BytesIO(data), dto.object_key, len(data), dto.bucket)
        except Exception:
            image_log.exception(
                "image.upload_failed", duration_seconds=elapsed(upload_started_at)
            )
            raise
        image_log.info(
            "image.upload_completed", duration_seconds=elapsed(upload_started_at)
        )

    try:
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
            app_limit=APP_LIMIT,
            batch_size=BATCH_SIZE,
            upload_workers=UPLOAD_WORKERS,
            pipeline_date=pipeline_date.isoformat(),
        )

        app = App(app_config=config, rate_limit_config=RateLimitConfig(20, 1))
        app.minio.create_or_ignore_bucket(IMAGE_BUCKET)
        pipeline = SteamAppPipeline(
            app.steam_list_resource, app.steam_app_details_resource
        )

        stage_started_at = perf_counter()
        log.info("steam.app_list_started")
        app_list = pipeline.get_list_apps(
            IStoreServiceGetAppListV1RequestDTO(), limit=APP_LIMIT
        )
        log.info(
            "steam.app_list_completed",
            batches=len(app_list),
            records=sum(len(b.records) for b in app_list),
            duration_seconds=elapsed(stage_started_at),
        )
        stage_started_at = perf_counter()
        log.info("steam.app_details_started")
        app_details = pipeline.get_list_apps_details(app_list)
        log.info(
            "steam.app_details_completed",
            batches=len(app_details),
            records=sum(len(b.records) for b in app_details),
            duration_seconds=elapsed(stage_started_at),
        )

        games = pipeline.iter_to_domain_games(pipeline.iter_raw_games(app_details))

        for batch_number, batch in enumerate(batched(games, BATCH_SIZE), start=1):
            batch_started_at = perf_counter()
            log.info("batch.started", batch_number=batch_number, games_count=len(batch))
            insert_started_at = perf_counter()

            inserted_games = app.postgres.insert_games(batch, source="steam")

            stats["games_inserted"] += len(inserted_games)
            stats["games_existing"] += len(batch) - len(inserted_games)
            log.info(
                "batch.games_saved",
                batch_number=batch_number,
                inserted=len(inserted_games),
                existing=len(batch) - len(inserted_games),
                duration_seconds=elapsed(insert_started_at),
            )
            for game, game_uuid in inserted_games:
                game_started_at = perf_counter()
                game_log = log.bind(
                    app_id=game.steam_id,
                    game_name=game.name,
                    game_uuid=str(game_uuid),
                    batch_number=batch_number,
                    pipeline_date=pipeline_date.isoformat(),
                )
                game_log.info(
                    "game.images_started",
                    expected_images=bool(game.header_image_url)
                    + len(game.screenshots or []),
                )
                header_image = None
                images_dto = []
                upload_jobs = []
                if game.header_image_url:
                    try:
                        header_image = fetch_image(game.header_image_url, game_log)
                        image_type = get_image_mime(header_image)
                        object_key = app.minio.build_object_key(
                            "game-catalog",
                            "steam",
                            "header_image",
                            pipeline_date,
                            f"{game_uuid}-header-image{IMAGE_EXTENSIONS[image_type]}",
                        )
                        upload_jobs.append(
                            (
                                header_image,
                                GameImageDTO(
                                    source_url=game.header_image_url,
                                    bucket="game-catalog",
                                    object_key=object_key,
                                    screenshot=False,
                                ),
                            )
                        )
                    except Exception:  # noqa: BLE001 - log failure and continue with other games
                        stats["games_images_skipped"] += 1
                        game_log.exception(
                            "game.images_skipped",
                            image_kind="header",
                            duration_seconds=elapsed(game_started_at),
                        )
                        continue
                if game.screenshots:
                    try:
                        for i, screen_url in enumerate(game.screenshots):
                            screen = fetch_image(screen_url, game_log)
                            image_type = get_image_mime(screen)
                            object_key = app.minio.build_object_key(
                                "game-catalog",
                                "steam",
                                "screen",
                                pipeline_date,
                                f"{game_uuid}-screen-{i}{IMAGE_EXTENSIONS[image_type]}",
                            )
                            upload_jobs.append(
                                (
                                    screen,
                                    GameImageDTO(
                                        source_url=screen_url,
                                        bucket="game-catalog",
                                        object_key=object_key,
                                        screenshot=True,
                                    ),
                                )
                            )
                    except Exception:  # noqa: BLE001 - log failure and continue with other games
                        stats["games_images_skipped"] += 1
                        game_log.exception(
                            "game.images_skipped",
                            image_kind="screenshot",
                            duration_seconds=elapsed(game_started_at),
                        )
                        continue
                with ThreadPoolExecutor(max_workers=UPLOAD_WORKERS) as executor:
                    futures = {
                        executor.submit(
                            upload_image,
                            data,
                            dto,
                            game_log,
                        ): (dto, len(data))
                        for data, dto in upload_jobs
                    }

                    for future in as_completed(futures):
                        dto, size_bytes = futures[future]

                        try:
                            future.result()
                            images_dto.append(dto)
                            stats["images_uploaded"] += 1
                            stats["uploaded_bytes"] += size_bytes
                        except Exception:  # noqa: BLE001 - log failure and continue with other games
                            stats["upload_errors"] += 1
                save_started_at = perf_counter()
                app.postgres.insert_images(game_uuid, images_dto)
                stats["image_records_saved"] += len(images_dto)
                stats["games_processed"] += 1
                game_log.info(
                    "game.image_records_saved",
                    records=len(images_dto),
                    table="game_image",
                    duration_seconds=elapsed(save_started_at),
                )
                game_log.info(
                    "game.completed",
                    images_uploaded=len(images_dto),
                    duration_seconds=elapsed(game_started_at),
                )
            stats["batches_processed"] += 1
            log.info(
                "batch.completed",
                batch_number=batch_number,
                duration_seconds=elapsed(batch_started_at),
                **stats,
            )
        status = (
            "completed_with_errors"
            if (
                stats["download_errors"]
                or stats["upload_errors"]
                or stats["games_images_skipped"]
            )
            else "completed"
        )
    except KeyboardInterrupt:
        status = "interrupted"
        log.warning("pipeline.interrupted")
        raise
    except Exception:
        log.exception("pipeline.failed")
        raise
    finally:
        log.info(
            "pipeline.summary",
            status=status,
            duration_seconds=elapsed(started_at),
            downloaded_mib=round(stats["downloaded_bytes"] / 1024**2, 3),
            uploaded_mib=round(stats["uploaded_bytes"] / 1024**2, 3),
            **stats,
        )


if __name__ == "__main__":
    main()
