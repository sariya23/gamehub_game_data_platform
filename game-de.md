# Schema: game de
Database: mysql
Tables: 14
Columns are NOT NULL unless marked nullable.

## game
id: uuid PK
name: text
full_description: text
short_description: text nullable
update_at: datetime
deleted_at: datetime nullable

## nsi_game_source
id: bigint PK auto unsigned
name: text
updated_at: datetime
deleted_at: datetime nullable

## game_source
id: bigint PK
source_id: bigint FK
game_id: uuid FK
external_id: text
updated_at: datetime
deleted_at: datetime nullable

## nsi_game_rating_source
id: bigint PK auto unsigned
name: text
min_value: decimal
max_value: decimal
update_at: datetime
deleted_at: datetime nullable

## game_rating
id: bigint PK
game_id: uuid FK
rating_source_id: bigint FK
value: decimal
url: text nullable
updated_at: datetime
deleted_at: datetime nullable

## game_release_date
id: bigint PK auto unsigned
game_id: uuid FK
release_date: date
comig_soon: boolean
updated_at: datetime
deleted_at: datetime nullable
platform_id: bigint FK

## nsi_game_platform
id: bigint PK auto unsigned
name: text
platform_type_id: bigint FK
updated_at: datetime
deleted_at: datetime nullable

## bridge_game_platform
platform_id: bigint FK
game_id: uuid FK
updated_at: datetime
deleted_at: datetime nullable

## game_developer
id: bigint PK auto unsigned
name: text
updated_at: datetime
deleted_at: datetime nullable

## bridge_game_developer
game_id: uuid FK
developer_id: bigint FK
updated_at: datetime
deleted_at: datetime nullable

## game_image
id: bigint PK
url: text
game_id: uuid FK
screenshot: boolean
updated_at: datetime
deleted_at: datetime nullable

## nsi_game_genre
id: bigint PK auto unsigned
name: text
updated_at: datetime
deleted_at: datetime

## bridge_game_genre
genre_id: bigint auto FK unsigned
game_id: uuid FK
updated_at: datetime
deleted_at: datetime nullable

## nsi_game_platform_type
id: bigint PK auto unsigned
name: text
update_at: bigint
deleted_at: bigint

## Relationships
game_source.source_id → nsi_game_source.id (many-to-one)
game_source.game_id → game.id (many-to-one)
game_rating.game_id → game.id (many-to-one)
nsi_game_rating_source.id → game_rating.rating_source_id (one-to-many)
game_release_date.game_id → game.id (one-to-one)
bridge_game_platform.platform_id → nsi_game_platform.id (many-to-one)
bridge_game_platform.game_id → game.id (many-to-one)
bridge_game_developer.game_id → game.id (many-to-one)
bridge_game_developer.developer_id → game_developer.id (many-to-one)
bridge_game_genre.genre_id → nsi_game_genre.id (many-to-one)
bridge_game_genre.game_id → game.id (many-to-one)
game_image.game_id → game.id (many-to-one)
nsi_game_platform.id → game_release_date.platform_id (one-to-one)
nsi_game_platform_type.id → nsi_game_platform.platform_type_id (one-to-many)

---
If you suggest changes to this schema, ALSO return them as a DrawSQL patch: one fenced ```json code block, so I can apply them to my diagram. If you are only answering a question, skip the patch.

Patch rules:
- One JSON object with "strategy": "merge"; combine every change into that single patch.
- Reference tables and columns by name. Only include what changes — omit unchanged columns and unused optional fields.
- Column: {"name","type","length","is_primary_key","is_auto_increment","is_nullable","is_unique_key","is_index","is_unsigned","default","enum_values"} — use exact type names for mysql as shown in the schema above.
- Relationship: {"type":"one-to-many","source_table":"users","source_column":"id","target_table":"posts","target_column":"user_id"} — for "one-to-many" the source is the "one" side; for "many-to-one" the source is the "many" (foreign-key) side. Prefer "one-to-many".
- Add "default_type" ("string" | "function" | "number" | "boolean") when a default could be misread — a literal string "CURRENT_TIMESTAMP" or "0" needs "default_type":"string".
- SET columns (MySQL) list their members in "set_values", not "enum_values".
- Index: {"indexes":[{"name":"idx_posts_user_created","type":"index","columns":["user_id","created_at"]}]} on its table — "type" is "index" or "unique"; delete via "deletions".
- Group: {"name":"Billing"}. A group never lists its members — put "parent_name":"Billing" on each table that belongs to it.
- Sticky note: {"sticky_notes":[{"content":"..."}]}.
- Delete via "deletions"; rename via "old_name". Do not include left/top coordinates.

Examples:
Add table: `{"strategy":"merge","tables":[{"name":"posts","comment":"Blog posts","columns":[{"name":"id","type":"bigint","is_primary_key":true,"is_auto_increment":true},{"name":"user_id","type":"bigint","is_index":true},{"name":"title","type":"varchar","length":255},{"name":"body","type":"text","is_nullable":true},{"name":"created_at","type":"timestamp","is_nullable":true},{"name":"updated_at","type":"timestamp","is_nullable":true}]}]}`
Rename table and column (use old_name only when renaming): `{"strategy":"merge","tables":[{"name":"articles","old_name":"posts","columns":[{"name":"content","old_name":"body"}]}]}`
Delete: `{"strategy":"merge","deletions":{"tables":["tmp"],"columns":[{"table":"users","columns":["legacy"]}],"relationships":[{"source_table":"users","source_column":"id","target_table":"posts","target_column":"user_id"}]}}`
Multiple groups with nested tables (every table sets parent_name): `{"strategy":"merge","groups":[{"name":"Auth"},{"name":"Content"}],"tables":[{"name":"users","parent_name":"Auth","columns":[{"name":"id","type":"bigint","is_primary_key":true,"is_auto_increment":true}]},{"name":"roles","parent_name":"Auth","columns":[{"name":"id","type":"bigint","is_primary_key":true,"is_auto_increment":true}]},{"name":"posts","parent_name":"Content","columns":[{"name":"id","type":"bigint","is_primary_key":true,"is_auto_increment":true}]}]}`
