from typing import Iterable, Sequence
from uuid import UUID, uuid4

import psycopg

from config import Config
from src.models.steam.game import Game, Genre


class PostgresClient:
    def __init__(self, config: Config) -> None:
        self.__conn = psycopg.connect(host=config.database.host, port=config.database.port,
                                      dbname=config.database.name, user=config.database.user, 
                                      password=config.database.password.get_secret_value())
    
    def close(self):
        self.__conn.close()
    

    def execute_many(self, query, rows: Iterable[tuple]) -> None:
        rows = list(rows)

        if not rows:
            return

        with self.__conn.cursor() as cur:
            cur.executemany(query, rows)

    def insert_game(
self,
        game: Game,
        *,
        steam_source_id: int,
        rating_source_ids: dict[str, int],
        platform_ids: dict[str, int],
    ) -> bool:
        with self.__conn.transaction():
            game_id = self.insert_game_row(
                game,
                steam_source_id,
            )

            if game_id is None:
                return False

            self.insert_developers(
                game_id,
                game.developers,
            )

            self.insert_genres(
                game_id,
                game.genres,
            )

            self.insert_ratings(
                game_id,
                game,
                rating_source_ids,
            )

            self.insert_images(
                game_id,
                game,
            )

            self.insert_platforms(
                game_id,
                game,
                platform_ids,
            )

            self.insert_release_dates(
                game_id,
                game,
                platform_ids,
            )

        return True


    def insert_game_row(
        self,
        game: Game,
        source_id: int,
    ):
        game_id = uuid4()

        row = self.__conn.execute(
            """
            INSERT INTO game (
                id,
                source_id,
                external_id,
                name,
                full_description,
                short_description
            )
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (source_id, external_id)
            WHERE deleted_at IS NULL
            DO NOTHING
            RETURNING id
            """,
            (
                game_id,
                source_id,
                str(game.steam_id),
                game.name,
                game.description,
                game.short_description,
            ),
        ).fetchone()

        if row is None:
            return None

        return row[0]

    def insert_images(
        self,
        game_id,
        game: Game,
    ) -> None:
        rows = []

        if game.header_image_url:
            rows.append(
                (
                    game_id,
                    game.header_image_url,
                    False,
                )
            )

        rows.extend(
            (
                game_id,
                url,
                True,
            )
            for url in game.screenshots
            if url
        )

        if not rows:
            return

        with self.__conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO game_image (
                    game_id,
                    source_url,
                    screenshot
                )
                VALUES (%s, %s, %s)
                """,
                rows,
            )

    def insert_genres(
        self,
        game_id,
        genres: list[Genre],
    ) -> None:
        names = list({
            genre.name
            for genre in genres
            if genre.name
        })

        if not names:
            return

        genre_ids = {}

        with self.__conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO nsi_game_genre (name)
                VALUES (%s)
                ON CONFLICT (name)
                WHERE deleted_at IS NULL
                DO UPDATE SET
                    name = EXCLUDED.name
                RETURNING id, name
                """,
                [(name,) for name in names],
                returning=True,
            )

            for result in cur.results():
                row = result.fetchone()

                if row is not None:
                    genre_id, name = row
                    genre_ids[name] = genre_id

        with self.__conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO bridge_game_genre (
                    game_id,
                    genre_id
                )
                VALUES (%s, %s)
                ON CONFLICT (game_id, genre_id)
                WHERE deleted_at IS NULL
                DO NOTHING
                """,
                [
                    (
                        game_id,
                        genre_ids[name],
                    )
                    for name in names
                ],
            )

    def insert_developers(
        self,
        game_id: UUID,
        developers: list[str],
    ) -> None:
        names = list({
            developer
            for developer in developers
            if developer
        })

        if not names:
            return

        developer_ids: dict[str, int] = {}

        with self.__conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO game_developer (name)
                VALUES (%s)
                ON CONFLICT (name)
                WHERE deleted_at IS NULL
                DO UPDATE SET
                    name = EXCLUDED.name
                RETURNING id, name
                """,
                [(name,) for name in names],
                returning=True,
            )

            for result in cur.results():
                row = result.fetchone()

                if row is None:
                    continue

                developer_id, name = row
                developer_ids[name] = developer_id

        with self.__conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO bridge_game_developer (
                    game_id,
                    developer_id
                )
                VALUES (%s, %s)
                ON CONFLICT (game_id, developer_id)
                WHERE deleted_at IS NULL
                DO NOTHING
                """,
                [
                    (
                        game_id,
                        developer_ids[name],
                    )
                    for name in names
                ],
            )

    def insert_ratings(
        self,
        game_id: UUID,
        game: Game,
        rating_source_ids: dict[str, int],
    ) -> None:
        rows = [
            (
                game_id,
                rating_source_ids["Steam"],
                game.recommendations,
                None,
            )
        ]

        if game.metacritic_score is not None:
            rows.append(
                (
                    game_id,
                    rating_source_ids["Metacritic"],
                    game.metacritic_score,
                    game.metacritic_url,
                )
            )

        with self.__conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO game_rating (
                    game_id,
                    rating_source_id,
                    value,
                    url
                )
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (game_id, rating_source_id)
                WHERE deleted_at IS NULL
                DO UPDATE SET
                    value = EXCLUDED.value,
                    url = EXCLUDED.url,
                    updated_at = NOW() AT TIME ZONE 'UTC'
                """,
                rows,
            )
    

    def insert_platforms(self,
        game_id: UUID,
        game: Game,
        platform_ids: dict[str, int],
    ) -> None:
        platform_names = game.get_game_platform_names()

        if not platform_names:
            return

        with self.__conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO bridge_game_platform (
                    game_id,
                    platform_id
                )
                VALUES (%s, %s)
                ON CONFLICT (game_id, platform_id)
                WHERE deleted_at IS NULL
                DO NOTHING
                """,
                [
                    (
                        game_id,
                        platform_ids[name],
                    )
                    for name in platform_names
                ],
            )

    def insert_release_dates(
        self,
        game_id: UUID,
        game: Game,
        platform_ids: dict[str, int],
    ) -> None:
        if game.release_date is None:
            return

        platform_names = game.get_game_platform_names()

        if not platform_names:
            return

        with self.__conn.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO game_release_date (
                    game_id,
                    platform_id,
                    release_date
                )
                VALUES (%s, %s, %s)
                ON CONFLICT (game_id, platform_id)
                WHERE deleted_at IS NULL
                DO UPDATE SET
                    release_date = EXCLUDED.release_date,
                    updated_at = NOW() AT TIME ZONE 'UTC'
                """,
                [
                    (
                        game_id,
                        platform_ids[name],
                        game.release_date,
                    )
                    for name in platform_names
                ],
            )