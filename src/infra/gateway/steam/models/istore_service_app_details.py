from pydantic import BaseModel, RootModel


class Requirements(BaseModel):
    minimum: str | None = None
    recommended: str | None = None


class PriceOverview(BaseModel):
    currency: str
    initial: int
    final: int
    discount_percent: int
    initial_formatted: str
    final_formatted: str


class PackageGroupSub(BaseModel):
    packageid: int
    percent_savings_text: str
    percent_savings: int
    option_text: str
    option_description: str
    can_get_free_license: str
    is_free_license: bool
    price_in_cents_with_discount: int


class PackageGroup(BaseModel):
    name: str
    title: str
    description: str
    selection_text: str
    save_text: str
    display_type: int
    is_recurring_subscription: str
    subs: list[PackageGroupSub]


class Platforms(BaseModel):
    windows: bool
    mac: bool
    linux: bool


class Metacritic(BaseModel):
    score: int
    url: str


class Category(BaseModel):
    id: int
    description: str


class Genre(BaseModel):
    id: str
    description: str


class Screenshot(BaseModel):
    id: int
    path_thumbnail: str
    path_full: str


class Recommendations(BaseModel):
    total: int


class ReleaseDate(BaseModel):
    coming_soon: bool
    date: str


class SupportInfo(BaseModel):
    url: str
    email: str


class ContentDescriptors(BaseModel):
    ids: list[int]
    notes: str | None = None


class Rating(BaseModel):
    rating: str | None = None
    rating_generated: str | None = None
    required_age: str | None = None
    banned: str | None = None
    use_age_gate: str | None = None
    descriptors: str | None = None


class AppDetails(BaseModel):
    type: str
    name: str
    steam_appid: int
    required_age: int
    is_free: bool

    detailed_description: str | None = None
    about_the_game: str | None = None
    short_description: str | None = None
    supported_languages: str | None = None

    header_image: str | None = None
    capsule_image: str | None = None
    capsule_imagev5: str | None = None
    website: str | None = None

    pc_requirements: Requirements | dict | list | None = None
    mac_requirements: Requirements | dict | list | None = None
    linux_requirements: Requirements | dict | list | None = None

    developers: list[str] | None = None
    publishers: list[str] | None = None

    price_overview: PriceOverview | None = None

    packages: list[int] | None = None
    package_groups: list[PackageGroup] | None = None

    platforms: Platforms | None = None
    metacritic: Metacritic | None = None

    categories: list[Category] | None = None
    genres: list[Genre] | None = None
    screenshots: list[Screenshot] | None = None

    recommendations: Recommendations | None = None
    release_date: ReleaseDate | None = None
    support_info: SupportInfo | None = None

    background: str | None = None
    background_raw: str | None = None

    content_descriptors: ContentDescriptors | None = None

    # Ключи здесь динамические: usk, pegi, esrb, dejus, ...
    ratings: dict[str, Rating] | None = None


class AppDetailsResult(BaseModel):
    success: bool
    data: AppDetails | None = None


class AppDetailsResponse(RootModel[dict[str, AppDetailsResult]]):
    pass