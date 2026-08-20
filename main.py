import httpx
import structlog

from config import load_config
from src.infra.gateway.steam.constants import STEAM_API_BASE_URL, STEAM_STORE_BASE_URL
from src.infra.gateway.steam.steam import SteamApi
from src.infra.s3.minio.create import create_minio
from src.resources.steam.steam import SteamAppListResource

log = structlog.get_logger()
config = load_config(".env.local")
log.info(f"start in '{config.env.type}' env")

m = create_minio(config=config.s3)

client = httpx.Client(timeout=config.steam.http.steam_api_response_timeout_seconds, headers={"x-webapi-key": config.steam.auth.steam_api_web_key.get_secret_value()})
steam_api = SteamApi(client=client, base_store_url=STEAM_STORE_BASE_URL, base_url_api=STEAM_API_BASE_URL)
steam_resource = SteamAppListResource(steam_api)
for i in steam_resource.iter_game_baches(10, 1):
    print(i)
    
