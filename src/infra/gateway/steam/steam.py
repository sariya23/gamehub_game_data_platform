import httpx

from src.types import Seconds


class SteamApi:
    def __init__(self, timeout: Seconds) -> None:
        self.__client = httpx.Client(timeout=timeout)
    
    def isotre_service_get_app_list_v1(self):
        pass