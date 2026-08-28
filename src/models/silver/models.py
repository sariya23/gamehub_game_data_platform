from datetime import date

from pydantic import BaseModel, ConfigDict

from src.lib.datetime.datetime import parse_release_date_from_human
from src.models.raw.models import (
    RawCategory,
    RawGenre,
    RawMetacritic,
    RawPlatforms,
    RawScreenshot,
    RawSteamApp,
)
from src.models.silver.exceptions import (
    SilverNameRequired,
    SilverReleaseDateRequired,
    SilverSteamAppIdRequired,
    SilverTypeRequired,
)


class SilverPlatforms(BaseModel):
    windows: bool | None
    mac: bool | None
    linux: bool | None

    @classmethod
    def from_raw(cls, raw: RawPlatforms):
        return cls(windows=raw.windows, mac=raw.mac, linux=raw.linux)


class SilverMetacritic(BaseModel):
    score: int | None
    url: str | None

    @classmethod
    def from_raw(cls, raw: RawMetacritic):
        return cls(score=raw.score, url=raw.url)


class SilverGenre(BaseModel):
    description: str | None

    @classmethod
    def from_raw(cls, raw: RawGenre):
        return cls(description=raw.description)


class SilverCategory(BaseModel):
    description: str | None

    @classmethod
    def from_raw(cls, raw: RawCategory):
        return cls(description=raw.description)


class SilverScreenshot(BaseModel):
    path_thumbnail: str | None
    path_full: str | None

    @classmethod
    def from_raw(cls, raw: RawScreenshot):
        return cls(path_thumbnail=raw.path_thumbnail, path_full=raw.path_full)


class SilverSteamApp(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    name: str
    steam_appid: int

    detailed_description: str | None = None
    short_description: str | None = None

    developers: list[str] | None = None

    platforms: SilverPlatforms | None = None
    metacritic: SilverMetacritic | None = None

    genres: list[SilverGenre] | None = None
    categories: list[SilverCategory] | None = None
    screenshots: list[SilverScreenshot] | None = None

    release_date: date
    coming_soon: bool | None = None

    @classmethod
    def from_raw(cls, raw: RawSteamApp):
        if not raw.type:
            raise SilverTypeRequired("'type' is required")
        if not raw.name:
            raise SilverNameRequired("'name' is required")
        if not raw.steam_appid:
            raise SilverSteamAppIdRequired("'steam_appid' is required")
        platforms = None
        if raw.platforms:
            platforms = SilverPlatforms.from_raw(raw.platforms)

        metacritic = None
        if raw.metacritic:
            metacritic = SilverMetacritic.from_raw(raw.metacritic)

        if not raw.release_date:
            raise SilverReleaseDateRequired("'release_date' is required")

        if not raw.release_date.date:
            raise SilverReleaseDateRequired("'release_date' is required")

        return cls(
            type=raw.type,
            name=raw.name,
            steam_appid=raw.steam_appid,
            detailed_description=raw.detailed_description,
            short_description=raw.short_description,
            developers=raw.developers,
            platforms=platforms,
            metacritic=metacritic,
            genres=[SilverGenre.from_raw(genre) for genre in raw.genres or []],
            categories=[
                SilverCategory.from_raw(category) for category in raw.categories or []
            ],
            screenshots=[
                SilverScreenshot.from_raw(screen) for screen in raw.screenshots or []
            ],
            release_date=parse_release_date_from_human(raw.release_date.date),
            coming_soon=raw.release_date.coming_soon,
        )
