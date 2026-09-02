import sqlite3

from nexus.config.settings import settings


class Database:
    """
    Gerenciador do banco de dados local do Nexus.
    """

    def __init__(self):
        settings.database_dir.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(
            settings.database_file
        )

    def initialize(self):
        cursor = self.connection.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS system_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        self.connection.commit()

    def add_event(self, event_type: str, message: str):
        cursor = self.connection.cursor()

        cursor.execute(
            """
            INSERT INTO system_events (event_type, message)
            VALUES (?, ?)
            """,
            (event_type, message),
        )

        self.connection.commit()

    def close(self):
        self.connection.close()
