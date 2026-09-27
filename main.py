import structlog

from io import BytesIO
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import load_config
from src.models.dto.game_image import GameImageDTO
from src.lib.image import get_image_mime, IMAGE_EXTENSIONS
from src.app.app import App
from src.infra.gateway.steam.models.api.i_store_service.get_app_list.v1.istore_service_get_app_list_v1 import (
    IStoreServiceGetAppListV1RequestDTO,
)
from src.lib.batched import batched
from src.lib.http import download_image
from src.lib.input.input import get_pipeline_date
from src.lib.logging.logging import configure_logging, register_secrets
from src.lib.rate_limit.rate_limit import RateLimitConfig
from src.pipeline.steam import SteamAppPipelineDebug

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

app = App(app_config=config, rate_limit_config=RateLimitConfig(20, 1))
app.minio.create_or_ignore_bucket("game-catalog")
pipeline = SteamAppPipelineDebug(app.steam_list_resource, app.steam_app_details_resource)

app_list = pipeline.get_list_apps(IStoreServiceGetAppListV1RequestDTO(), limit=10)
app_details = pipeline.get_list_apps_details(app_list)

BATCH_SIZE = 100
games = pipeline.iter_to_domain_games(pipeline.iter_raw_games(app_details))
source_ids = app.postgres.get_source_ids()


for batch in batched(games, BATCH_SIZE):
    source_id = source_ids["steam"]

    games = app.postgres.insert_games(
        batch,
        source="steam"
    )

    for game, game_uuid in games:
        header_image = None
        images_dto = []
        upload_jobs = []
        if game.header_image_url:
            try:
                header_image = download_image(game.header_image_url)
                image_type = get_image_mime(header_image)
                object_key = app.minio.build_object_key("game-catalog", "steam", "header_image", pipeline_date,
                                                        f"{game_uuid}-header-image{IMAGE_EXTENSIONS[image_type]}")
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
            except Exception as e:
                log.exception(f"error while load header image {e}")
                continue
        if game.screenshots:
            try:
                for i, screen_url in enumerate(game.screenshots):
                    screen = download_image(screen_url)
                    image_type = get_image_mime(screen)
                    object_key = app.minio.build_object_key("game-catalog", "steam", "screen", pipeline_date,
                                                            f"{game_uuid}-screen-{i}{IMAGE_EXTENSIONS[image_type]}")
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
            except Exception as e:
                log.exception(f"error while load screen {e}")
                continue
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                executor.submit(
                    app.minio.upload_file,
                    BytesIO(data),
                    dto.object_key,
                    len(data),
                    dto.bucket,
                ): dto
                for data, dto in upload_jobs
            }

            for future in as_completed(futures):
                dto = futures[future]

                try:
                    future.result()
                    images_dto.append(dto)
                except Exception:
                    log.exception(
                        "Failed to upload image %s",
                        dto.source_url,
                    )
        app.postgres.insert_images(game_uuid, images_dto)
