BEGIN;

-- ============================================================
-- DATE
-- ============================================================

CREATE TABLE dim_date (
    date_key        INTEGER PRIMARY KEY, -- YYYYMMDD
    date            DATE NOT NULL UNIQUE,
    day             SMALLINT NOT NULL,
    month           SMALLINT NOT NULL,
    month_name      VARCHAR(20) NOT NULL,
    quarter         SMALLINT NOT NULL,
    year            SMALLINT NOT NULL,
    day_of_week     SMALLINT NOT NULL,

    CONSTRAINT chk_dim_date_day
        CHECK (day BETWEEN 1 AND 31),

    CONSTRAINT chk_dim_date_month
        CHECK (month BETWEEN 1 AND 12),

    CONSTRAINT chk_dim_date_quarter
        CHECK (quarter BETWEEN 1 AND 4),

    CONSTRAINT chk_dim_date_day_of_week
        CHECK (day_of_week BETWEEN 1 AND 7)
);


-- ============================================================
-- GAME
-- game_id генерируется приложением / ETL
-- ============================================================

CREATE TABLE dim_game (
    game_id                 UUID PRIMARY KEY,

    name                    TEXT NOT NULL,
    short_description       TEXT,
    detailed_description    TEXT,

    release_date_key        INTEGER,

    CONSTRAINT fk_dim_game_release_date
        FOREIGN KEY (release_date_key)
        REFERENCES dim_date(date_key)
);


-- ============================================================
-- SOURCE
-- Steam, PlayStation Store и т.д.
-- ============================================================

CREATE TABLE dim_source (
    source_id       SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            VARCHAR(100) NOT NULL UNIQUE
);


CREATE TABLE game_source (
    game_id         UUID NOT NULL,
    source_id       SMALLINT NOT NULL,
    external_id     VARCHAR(255) NOT NULL,

    PRIMARY KEY (game_id, source_id),

    CONSTRAINT uq_game_source_external_id
        UNIQUE (source_id, external_id),

    CONSTRAINT fk_game_source_game
        FOREIGN KEY (game_id)
        REFERENCES dim_game(game_id),

    CONSTRAINT fk_game_source_source
        FOREIGN KEY (source_id)
        REFERENCES dim_source(source_id)
);


-- ============================================================
-- DEVELOPER
-- ============================================================

CREATE TABLE dim_developer (
    developer_id    BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            TEXT NOT NULL UNIQUE
);


CREATE TABLE bridge_game_developer (
    game_id         UUID NOT NULL,
    developer_id    BIGINT NOT NULL,

    PRIMARY KEY (game_id, developer_id),

    CONSTRAINT fk_bridge_game_developer_game
        FOREIGN KEY (game_id)
        REFERENCES dim_game(game_id),

    CONSTRAINT fk_bridge_game_developer_developer
        FOREIGN KEY (developer_id)
        REFERENCES dim_developer(developer_id)
);


-- ============================================================
-- GENRE
-- ============================================================

CREATE TABLE dim_genre (
    genre_id        BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            VARCHAR(255) NOT NULL UNIQUE
);


CREATE TABLE bridge_game_genre (
    game_id         UUID NOT NULL,
    genre_id        BIGINT NOT NULL,

    PRIMARY KEY (game_id, genre_id),

    CONSTRAINT fk_bridge_game_genre_game
        FOREIGN KEY (game_id)
        REFERENCES dim_game(game_id),

    CONSTRAINT fk_bridge_game_genre_genre
        FOREIGN KEY (genre_id)
        REFERENCES dim_genre(genre_id)
);


-- ============================================================
-- CATEGORY
-- Single-player, Steam Achievements, Steam Cloud и т.д.
-- ============================================================

CREATE TABLE dim_category (
    category_id     BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            VARCHAR(255) NOT NULL UNIQUE
);


CREATE TABLE bridge_game_category (
    game_id         UUID NOT NULL,
    category_id     BIGINT NOT NULL,

    PRIMARY KEY (game_id, category_id),

    CONSTRAINT fk_bridge_game_category_game
        FOREIGN KEY (game_id)
        REFERENCES dim_game(game_id),

    CONSTRAINT fk_bridge_game_category_category
        FOREIGN KEY (category_id)
        REFERENCES dim_category(category_id)
);


-- ============================================================
-- PLATFORM
-- Windows, macOS, Linux
-- ============================================================

CREATE TABLE dim_platform (
    platform_id     SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name            VARCHAR(100) NOT NULL UNIQUE
);


CREATE TABLE bridge_game_platform (
    game_id         UUID NOT NULL,
    platform_id     SMALLINT NOT NULL,

    PRIMARY KEY (game_id, platform_id),

    CONSTRAINT fk_bridge_game_platform_game
        FOREIGN KEY (game_id)
        REFERENCES dim_game(game_id),

    CONSTRAINT fk_bridge_game_platform_platform
        FOREIGN KEY (platform_id)
        REFERENCES dim_platform(platform_id)
);


-- ============================================================
-- RATING SOURCE
-- Metacritic, OpenCritic и т.д.
-- ============================================================

CREATE TABLE dim_rating_source (
    rating_source_id    SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name                VARCHAR(100) NOT NULL UNIQUE
);


-- ============================================================
-- GAME RATING FACT
-- Оценка игры от конкретного источника на конкретную дату
-- ============================================================

CREATE TABLE fact_game_rating (
    game_id             UUID NOT NULL,
    rating_source_id    SMALLINT NOT NULL,
    snapshot_date_key   INTEGER NOT NULL,

    score               NUMERIC(5, 2),
    url                 TEXT,

    PRIMARY KEY (
        game_id,
        rating_source_id,
        snapshot_date_key
    ),

    CONSTRAINT fk_fact_game_rating_game
        FOREIGN KEY (game_id)
        REFERENCES dim_game(game_id),

    CONSTRAINT fk_fact_game_rating_source
        FOREIGN KEY (rating_source_id)
        REFERENCES dim_rating_source(rating_source_id),

    CONSTRAINT fk_fact_game_rating_date
        FOREIGN KEY (snapshot_date_key)
        REFERENCES dim_date(date_key)
);


-- ============================================================
-- SCREENSHOTS
-- ============================================================

CREATE TABLE game_screenshot (
    screenshot_id   BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,

    game_id         UUID NOT NULL,

    thumbnail_url   TEXT,
    full_url        TEXT NOT NULL,
    position        SMALLINT,

    CONSTRAINT fk_game_screenshot_game
        FOREIGN KEY (game_id)
        REFERENCES dim_game(game_id),

    CONSTRAINT uq_game_screenshot_position
        UNIQUE (game_id, position)
);


-- ============================================================
-- INDEXES
-- PostgreSQL создаёт индексы для PK и UNIQUE автоматически,
-- но не создаёт их автоматически для FK.
-- ============================================================

CREATE INDEX idx_dim_game_release_date
    ON dim_game(release_date_key);

CREATE INDEX idx_game_source_source
    ON game_source(source_id);

CREATE INDEX idx_bridge_game_developer_developer
    ON bridge_game_developer(developer_id);

CREATE INDEX idx_bridge_game_genre_genre
    ON bridge_game_genre(genre_id);

CREATE INDEX idx_bridge_game_category_category
    ON bridge_game_category(category_id);

CREATE INDEX idx_bridge_game_platform_platform
    ON bridge_game_platform(platform_id);

CREATE INDEX idx_fact_game_rating_source
    ON fact_game_rating(rating_source_id);

CREATE INDEX idx_fact_game_rating_date
    ON fact_game_rating(snapshot_date_key);

CREATE INDEX idx_game_screenshot_game
    ON game_screenshot(game_id);


-- ============================================================
-- INITIAL DICTIONARY DATA
-- ============================================================

INSERT INTO dim_source (name)
VALUES ('Steam');


INSERT INTO dim_platform (name)
VALUES
    ('Windows'),
    ('macOS'),
    ('Linux');


INSERT INTO dim_rating_source (name)
VALUES ('Metacritic');


COMMIT;