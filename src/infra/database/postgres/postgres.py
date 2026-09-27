from typing import Sequence
from uuid import UUID

import psycopg

from config import Config
from src.models.steam.game import Game


class PostgresClient:
    def __init__(self, config: Config) -> None:
        self.__conn = psycopg.connect(host=config.database.host, port=config.database.port,
                                      dbname=config.database.name, user=config.database.user, 
                                      password=config.database.password.get_secret_value())
    
    def close(self):
        self.__conn.close()
    

    def insert_games(self, games: Sequence[Game]) -> None:
        if not games:
            return

        game_ids = upsert_games(games)

        insert_developers(games, game_ids)
        insert_genres(games, game_ids)
        insert_ratings(games, game_ids)
        insert_images(games, game_ids)
        insert_platforms(games, game_ids)
        insert_release_dates(games, game_ids)

    def upsert_games(self, games: Sequence[Game]) -> dict[int, UUID]:
        steam_source_id = get_source_id(conn, "Steam")

        game_ids = get_existing_game_ids(
            conn,
            steam_source_id,
            games,
        )

        new_games = [
            game
            for game in games
            if game.steam_id not in game_ids
        ]

        existing_games = [
            game
            for game in games
            if game.steam_id in game_ids
        ]

        # Обновляем существующие игры батчем
        execute_many(
            conn,
            """
            UPDATE game
            SET
                name = %s,
                full_description = %s,
                short_description = %s,
                updated_at = NOW() AT TIME ZONE 'UTC'
            WHERE id = %s
            """,
            (
                (
                    game.name,
                    game.description,
                    game.short_description,
                    game_ids[game.steam_id],
                )
                for game in existing_games
            ),
        )

        # Новые игры вставляем батчем и получаем UUID
        returned = execute_many_returning(
            conn,
            """
            INSERT INTO game (
                name,
                full_description,
                short_description
            )
            VALUES (%s, %s, %s)
            RETURNING id
            """,
            (
                (
                    game.name,
                    game.description,
                    game.short_description,
                )
                for game in new_games
            ),
        )

        new_ids = [
            row[0]
            for row in returned
        ]

        for game, game_id in zip(new_games, new_ids):
            game_ids[game.steam_id] = game_id

        # game_source тоже одной пачкой
        execute_many(
            conn,
            """
            INSERT INTO game_source (
                source_id,
                game_id,
                external_id
            )
            VALUES (%s, %s, %s)
            ON CONFLICT (source_id, external_id)
            WHERE deleted_at IS NULL
            DO UPDATE SET
                game_id = EXCLUDED.game_id,
                updated_at = NOW() AT TIME ZONE 'UTC'
            """,
            (
                (
                    steam_source_id,
                    game_ids[game.steam_id],
                    str(game.steam_id),
                )
                for game in new_games
            ),
        )

        return game_ids