from datetime import date

from pydantic import BaseModel, Field


class Genre(BaseModel):
    steam_id: int | None = None
    name: str | None = None

class Rating(BaseModel):
    source: str
    value: int | None = None
    url: str | None = None

class Game(BaseModel):
    name: str
    steam_id: int

    description: str | None = None
    short_description: str | None = None
    header_image_url: str | None = None

    developers: list[str] = Field(default_factory=list)

    ratings: list[Rating] = Field(default_factory=list)

    genres: list[Genre] = Field(default_factory=list)
    screenshots: list[str] = Field(default_factory=list)

    release_date: date | None = None

    steam_url: str

    available_on_windows: bool | None = False
    available_on_mac: bool | None = False
    available_on_linux: bool | None = False

    def get_game_platform_names(self) -> list[str]:
        platforms = []

        if self.available_on_windows:
            platforms.append("windows")

        if self.available_on_mac:
            platforms.append("macos")

        if self.available_on_linux:
            platforms.append("linux")

        return platforms