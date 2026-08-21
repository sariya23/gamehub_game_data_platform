from typing import Any

from pydantic import BaseModel, ConfigDict, RootModel
from datetime import datetime


class RawBatch(BaseModel):
    source: str
    resource: str
    extracted_at: datetime
    records: list[dict[str, Any]]



class RawBaseModel(BaseModel):
    model_config = ConfigDict(extra="allow")


class RawRequirements(RawBaseModel):
    minimum: str | None = None
    recommended: str | None = None


class RawPriceOverview(RawBaseModel):
    currency: str | None = None
    initial: int | None = None
    final: int | None = None
    discount_percent: int | None = None
    initial_formatted: str | None = None
    final_formatted: str | None = None


class RawPackageSub(RawBaseModel):
    packageid: int | None = None
    percent_savings_text: str | None = None
    percent_savings: int | None = None
    option_text: str | None = None
    option_description: str | None = None

    # В Steam приходит строкой: "0"
    can_get_free_license: str | None = None

    is_free_license: bool | None = None
    price_in_cents_with_discount: int | None = None


class RawPackageGroup(RawBaseModel):
    name: str | None = None
    title: str | None = None
    description: str | None = None
    selection_text: str | None = None
    save_text: str | None = None
    display_type: int | None = None

    # В Steam приходит строкой: "false"
    is_recurring_subscription: str | None = None

    subs: list[RawPackageSub] | None = None


class RawPlatforms(RawBaseModel):
    windows: bool | None = None
    mac: bool | None = None
    linux: bool | None = None


class RawMetacritic(RawBaseModel):
    score: int | None = None
    url: str | None = None


class RawCategory(RawBaseModel):
    id: int | None = None
    description: str | None = None


class RawGenre(RawBaseModel):
    # В Steam приходит строкой: "1"
    id: str | None = None
    description: str | None = None


class RawScreenshot(RawBaseModel):
    id: int | None = None
    path_thumbnail: str | None = None
    path_full: str | None = None


class RawRecommendations(RawBaseModel):
    total: int | None = None


class RawReleaseDate(RawBaseModel):
    coming_soon: bool | None = None
    date: str | None = None


class RawSupportInfo(RawBaseModel):
    url: str | None = None
    email: str | None = None


class RawContentDescriptors(RawBaseModel):
    ids: list[int] | None = None
    notes: str | None = None


class RawRating(RawBaseModel):
    rating: str | None = None
    rating_generated: str | None = None
    required_age: str | None = None
    banned: str | None = None
    use_age_gate: str | None = None
    descriptors: str | None = None


class RawSteamApp(RawBaseModel):
    type: str | None = None
    name: str | None = None
    steam_appid: int | None = None
    required_age: int | None = None
    is_free: bool | None = None

    detailed_description: str | None = None
    about_the_game: str | None = None
    short_description: str | None = None
    supported_languages: str | None = None

    header_image: str | None = None
    capsule_image: str | None = None
    capsule_imagev5: str | None = None
    website: str | None = None

    # Steam иногда способен менять структуру подобных полей,
    # поэтому допускаем и пустой list.
    pc_requirements: RawRequirements | list[Any] | None = None
    mac_requirements: RawRequirements | list[Any] | None = None
    linux_requirements: RawRequirements | list[Any] | None = None

    developers: list[str] | None = None
    publishers: list[str] | None = None

    price_overview: RawPriceOverview | None = None

    packages: list[int] | None = None
    package_groups: list[RawPackageGroup] | None = None

    platforms: RawPlatforms | None = None
    metacritic: RawMetacritic | None = None

    categories: list[RawCategory] | None = None
    genres: list[RawGenre] | None = None
    screenshots: list[RawScreenshot] | None = None

    recommendations: RawRecommendations | None = None
    release_date: RawReleaseDate | None = None

    support_info: RawSupportInfo | None = None

    background: str | None = None
    background_raw: str | None = None

    content_descriptors: RawContentDescriptors | None = None

    # Ключи динамические:
    # usk, deJus, steam_germany, igrs и т.д.
    ratings: dict[str, RawRating] | None = None


class RawSteamAppResponse(RawBaseModel):
    success: bool | None = None
    data: RawSteamApp | None = None


class RawSteamAppLine(RootModel[dict[int, RawSteamAppResponse]]):
    pass
    