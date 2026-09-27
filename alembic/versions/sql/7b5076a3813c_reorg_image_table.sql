ALTER TABLE game_image
    ADD COLUMN bucket VARCHAR(63),
    ADD COLUMN object_key TEXT;

ALTER TABLE game_image
    DROP COLUMN storage_url;