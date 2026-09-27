BEGIN;

DROP TABLE game_source;

ALTER TABLE game
    ADD COLUMN source_id BIGINT NOT NULL,
    ADD COLUMN external_id TEXT NOT NULL;

ALTER TABLE game
    ADD CONSTRAINT fk_game_source_id
        FOREIGN KEY (source_id)
        REFERENCES nsi_game_source(id);

CREATE UNIQUE INDEX uq_game_source_external_active
    ON game (source_id, external_id)
    WHERE deleted_at IS NULL;

COMMIT;