INSERT INTO nsi_game_platform (name, platform_type_id)
SELECT platform.name, platform_type.id
FROM (VALUES
    ('pc', 'pc'),
    ('ps5', 'console'),
    ('ps4', 'console'),
    ('ps3', 'console'),
    ('xbox360', 'console'),
    ('nintendo_switch', 'console'),
    ('nintendo_switch_2', 'console')
) AS platform(name, type_name)
JOIN nsi_game_platform_type AS platform_type
    ON platform_type.name = platform.type_name
WHERE platform_type.deleted_at IS NULL;
