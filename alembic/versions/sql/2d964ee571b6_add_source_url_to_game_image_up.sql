ALTER TABLE game_image
RENAME COLUMN url TO storage_url;

ALTER TABLE game_image
ADD COLUMN source_url TEXT;