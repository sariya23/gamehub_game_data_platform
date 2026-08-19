from pydantic import BaseModel, Field


class IStoreServiceGetAppListV1ResponseSteamApp(BaseModel):
    app_id: int = Field(validation_alias="appid")
    name: str
    last_modified: int
    price_change_number: int


class IStoreServiceGetAppListV1Response(BaseModel):
    apps: list[IStoreServiceGetAppListV1ResponseSteamApp]
    have_more_results: bool
    last_appid: int


class IStoreServiceGetAppListV1ResponseDTO(BaseModel):
    response: IStoreServiceGetAppListV1Response


class IStoreServiceGetAppListV1RequestDTO(BaseModel):
    """
    src: https://partner.steamgames.com/doc/webapi/IStoreService
    """
    if_modified_since: int | None = Field(
        default=None,
        ge=0,
        le=4_294_967_295,
    )

    have_description_language: str | None = None

    include_games: bool = True
    include_dlc: bool = False
    include_software: bool = False
    include_videos: bool = False
    include_hardware: bool = False

    last_appid: int | None = Field(
        default=None,
        ge=0,
        le=4_294_967_295,
    )

    max_results: int = Field(
        default=10_000,
        ge=1,
        le=50_000,
    )
    
