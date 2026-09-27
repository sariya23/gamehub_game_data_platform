ALTER TABLE image
    ADD COLUMN bucket VARCHAR(63),
    ADD COLUMN object_key TEXT;

ALTER TABLE image
    DROP COLUMN storage_url;