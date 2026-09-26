BEGIN;

CREATE EXTENSION IF NOT EXISTS pgcrypto;


-- ============================================================
-- GAME
-- ============================================================

CREATE TABLE game (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name              TEXT NOT NULL,
    full_description  TEXT,
    short_description TEXT,

    updated_at        TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    deleted_at        TIMESTAMP
);


-- ============================================================
-- GENRE
-- ============================================================

CREATE TABLE nsi_game_genre (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name       TEXT NOT NULL,

    updated_at TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    deleted_at TIMESTAMP
);

CREATE UNIQUE INDEX uq_nsi_game_genre_name_active
    ON nsi_game_genre (name)
    WHERE deleted_at IS NULL;


CREATE TABLE bridge_game_genre (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    genre_id   BIGINT NOT NULL,
    game_id    UUID NOT NULL,

    updated_at TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    deleted_at TIMESTAMP,

    CONSTRAINT fk_bridge_game_genre_game
        FOREIGN KEY (game_id)
        REFERENCES game (id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_bridge_game_genre_genre
        FOREIGN KEY (genre_id)
        REFERENCES nsi_game_genre (id)
        ON DELETE RESTRICT
);

CREATE UNIQUE INDEX uq_bridge_game_genre_active
    ON bridge_game_genre (game_id, genre_id)
    WHERE deleted_at IS NULL;

CREATE INDEX ix_bridge_game_genre_game_id
    ON bridge_game_genre (game_id);

CREATE INDEX ix_bridge_game_genre_genre_id
    ON bridge_game_genre (genre_id);


-- ============================================================
-- PLATFORM TYPE
-- ============================================================

CREATE TABLE nsi_game_platform_type (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name       TEXT NOT NULL,

    updated_at TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    deleted_at TIMESTAMP
);

CREATE UNIQUE INDEX uq_nsi_game_platform_type_name_active
    ON nsi_game_platform_type (name)
    WHERE deleted_at IS NULL;


-- ============================================================
-- PLATFORM
-- ============================================================

CREATE TABLE nsi_game_platform (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name             TEXT NOT NULL,
    platform_type_id BIGINT NOT NULL,

    updated_at       TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    deleted_at       TIMESTAMP,

    CONSTRAINT fk_nsi_game_platform_platform_type
        FOREIGN KEY (platform_type_id)
        REFERENCES nsi_game_platform_type (id)
        ON DELETE RESTRICT
);

CREATE UNIQUE INDEX uq_nsi_game_platform_name_active
    ON nsi_game_platform (name)
    WHERE deleted_at IS NULL;

CREATE INDEX ix_nsi_game_platform_platform_type_id
    ON nsi_game_platform (platform_type_id);


CREATE TABLE bridge_game_platform (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    platform_id BIGINT NOT NULL,
    game_id     UUID NOT NULL,

    updated_at  TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    deleted_at  TIMESTAMP,

    CONSTRAINT fk_bridge_game_platform_game
        FOREIGN KEY (game_id)
        REFERENCES game (id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_bridge_game_platform_platform
        FOREIGN KEY (platform_id)
        REFERENCES nsi_game_platform (id)
        ON DELETE RESTRICT
);

CREATE UNIQUE INDEX uq_bridge_game_platform_active
    ON bridge_game_platform (game_id, platform_id)
    WHERE deleted_at IS NULL;

CREATE INDEX ix_bridge_game_platform_game_id
    ON bridge_game_platform (game_id);

CREATE INDEX ix_bridge_game_platform_platform_id
    ON bridge_game_platform (platform_id);


-- ============================================================
-- RELEASE DATE
-- ============================================================

CREATE TABLE game_release_date (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    game_id      UUID NOT NULL,
    platform_id  BIGINT NOT NULL,
    release_date DATE,
    coming_soon  BOOLEAN NOT NULL DEFAULT FALSE,

    updated_at   TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    deleted_at   TIMESTAMP,

    CONSTRAINT fk_game_release_date_game
        FOREIGN KEY (game_id)
        REFERENCES game (id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_game_release_date_platform
        FOREIGN KEY (platform_id)
        REFERENCES nsi_game_platform (id)
        ON DELETE RESTRICT
);

CREATE UNIQUE INDEX uq_game_release_date_game_platform_active
    ON game_release_date (game_id, platform_id)
    WHERE deleted_at IS NULL;

CREATE INDEX ix_game_release_date_game_id
    ON game_release_date (game_id);

CREATE INDEX ix_game_release_date_platform_id
    ON game_release_date (platform_id);


-- ============================================================
-- GAME SOURCE TYPE
-- Steam / Epic / GOG / etc.
-- ============================================================

CREATE TABLE nsi_game_source (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name       TEXT NOT NULL,

    updated_at TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'UTC'),
    deleted_at TIMESTAMP
);

CREATE UNIQUE INDEX uq_nsi_game_source_name_active
    ON nsi_game_source (name)
    WHERE deleted_at IS NULL;


-- ============================================================
-- GAME <-> SOURCE
-- ============================================================

CREATE TABLE game_source (
    id          BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    game_id     UUID NOT NULL,
    source_id   BIGINT NOT NULL,
    external_id TEXT NOT NULL,
    url         TEXT,

    updated_at  TIMESTAMP NOT NULL
        DEFAULT (NOW() AT TIME ZONE 'UTC'),

    deleted_at  TIMESTAMP,

    CONSTRAINT fk_game_source_game
        FOREIGN KEY (game_id)
        REFERENCES game(id),

    CONSTRAINT fk_game_source_source
        FOREIGN KEY (source_id)
        REFERENCES nsi_game_source(id)
);

-- Один внешний ID одного источника относится только к одной игре.
CREATE UNIQUE INDEX uq_game_source_external_active
    ON game_source (source_id, external_id)
    WHERE deleted_at IS NULL;

CREATE INDEX ix_game_source_game_id
    ON game_source (game_id);

CREATE INDEX ix_game_source_source_id
    ON game_source (source_id);


-- ============================================================
-- RATING SOURCE
-- Metacritic / OpenCritic / etc.
-- ============================================================

CREATE TABLE nsi_game_rating_source (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name       TEXT NOT NULL,
    min_value  NUMERIC NOT NULL,
    max_value  NUMERIC NOT NULL,

    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP,

    CONSTRAINT ck_nsi_game_rating_source_range
        CHECK (min_value < max_value)
);

CREATE UNIQUE INDEX uq_nsi_game_rating_source_name_active
    ON nsi_game_rating_source (name)
    WHERE deleted_at IS NULL;


-- ============================================================
-- GAME RATING
-- ============================================================

CREATE TABLE game_rating (
    id               BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    game_id          UUID NOT NULL,
    rating_source_id BIGINT NOT NULL,
    value            NUMERIC NOT NULL,
    url              TEXT,

    updated_at       TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at       TIMESTAMP,

    CONSTRAINT fk_game_rating_game
        FOREIGN KEY (game_id)
        REFERENCES game (id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_game_rating_rating_source
        FOREIGN KEY (rating_source_id)
        REFERENCES nsi_game_rating_source (id)
        ON DELETE RESTRICT
);

CREATE UNIQUE INDEX uq_game_rating_game_source_active
    ON game_rating (game_id, rating_source_id)
    WHERE deleted_at IS NULL;

CREATE INDEX ix_game_rating_game_id
    ON game_rating (game_id);

CREATE INDEX ix_game_rating_rating_source_id
    ON game_rating (rating_source_id);


-- ============================================================
-- GAME IMAGE
-- ============================================================

CREATE TABLE game_image (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    game_id    UUID NOT NULL,
    url        TEXT NOT NULL,
    screenshot BOOLEAN NOT NULL DEFAULT TRUE,

    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP,

    CONSTRAINT fk_game_image_game
        FOREIGN KEY (game_id)
        REFERENCES game (id)
        ON DELETE RESTRICT
);

CREATE UNIQUE INDEX uq_game_image_game_url_active
    ON game_image (game_id, url)
    WHERE deleted_at IS NULL;

CREATE INDEX ix_game_image_game_id
    ON game_image (game_id);


-- ============================================================
-- DEVELOPER
-- ============================================================

CREATE TABLE game_developer (
    id         BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name       TEXT NOT NULL,

    updated_at TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP
);

CREATE UNIQUE INDEX uq_game_developer_name_active
    ON game_developer (name)
    WHERE deleted_at IS NULL;


CREATE TABLE bridge_game_developer (
    id           BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    game_id      UUID NOT NULL,
    developer_id BIGINT NOT NULL,

    updated_at   TIMESTAMP NOT NULL DEFAULT NOW(),
    deleted_at   TIMESTAMP,

    CONSTRAINT fk_bridge_game_developer_game
        FOREIGN KEY (game_id)
        REFERENCES game (id)
        ON DELETE RESTRICT,

    CONSTRAINT fk_bridge_game_developer_developer
        FOREIGN KEY (developer_id)
        REFERENCES game_developer (id)
        ON DELETE RESTRICT
);

CREATE UNIQUE INDEX uq_bridge_game_developer_active
    ON bridge_game_developer (game_id, developer_id)
    WHERE deleted_at IS NULL;

CREATE INDEX ix_bridge_game_developer_game_id
    ON bridge_game_developer (game_id);

CREATE INDEX ix_bridge_game_developer_developer_id
    ON bridge_game_developer (developer_id);


COMMIT;