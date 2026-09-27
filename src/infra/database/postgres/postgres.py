import psycopg

from config import Config


class PostgresClient:
    def __init__(self, config: Config) -> None:
        self.__conn = psycopg.connect(host=config.database.host, port=config.database.port,
                                      dbname=config.database.name, user=config.database.user, 
                                      password=config.database.password.get_secret_value())
    
    def close(self):
        self.__conn.close()