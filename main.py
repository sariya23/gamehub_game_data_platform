from config import load_config
from src.infra.gateway.steam.constants import STEAM_API_BASE_URL, STEAM_STORE_BASE_URL
from src.infra.gateway.steam.models.api.i_store_service.get_app_list.v1.istore_service_get_app_list_v1 import (
                        IStoreServiceGetAppListV1RequestDTO,
)
from src.infra.gateway.steam.steam import SteamApi

config = load_config(".env.local")
steam_client = SteamApi(timeout=config.steam_api_response_timeout_seconds,
                        web_api_token=config.steam_api_web_key.get_secret_value(), base_url_api=STEAM_API_BASE_URL, base_store_url=STEAM_STORE_BASE_URL)
print(steam_client.isotre_service_get_app_list_v1(request=IStoreServiceGetAppListV1RequestDTO(max_results=1)))