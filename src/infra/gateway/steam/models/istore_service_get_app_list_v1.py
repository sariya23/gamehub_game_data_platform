from pydantic import BaseModel


class IStoreServiceGetAppListV1ResponseSteamApp(BaseModel):
    app_id: int
    name: str
    last_modified: int
    price_change_number: int


class IStoreServiceGetAppListV1Response(BaseModel):
    apps: list[IStoreServiceGetAppListV1ResponseSteamApp]
    have_more_results: bool
    last_appid: int


class IStoreServiceGetAppListV1ResponseDTO(BaseModel):
    response: IStoreServiceGetAppListV1Response