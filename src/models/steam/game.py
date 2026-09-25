from datetime import date

from pydantic import BaseModel, Field


class Genre(BaseModel):
    steam_id: int | None = None
    name: str | None = None


class Game(BaseModel):
    name: str
    steam_id: int

    description: str | None = None
    short_description: str | None = None
    header_image_url: str | None = None

    developers: list[str] = Field(default_factory=list)

    metacritic_score: int | None = None
    metacritic_url: str | None = None

    genres: list[Genre] = Field(default_factory=list)
    screenshots: list[str] = Field(default_factory=list)

    recommendations: int = 0

    release_date: date | None = None

    steam_url: str

    available_on_windows: bool | None = False
    available_on_mac: bool | None = False
    available_on_linux: bool | None = False
    