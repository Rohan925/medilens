import logging
import os

import psycopg


logger = logging.getLogger("db")

DEFAULT_DATABASE_URL = "postgresql://medilens:medilens123@127.0.0.1:5432/medilens_db"


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def get_connection() -> psycopg.Connection:
    return psycopg.connect(get_database_url())


def init_db() -> None:
    logger.info("DB init start")
    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id UUID PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                )
                """
            )
        connection.commit()
    logger.info("DB init complete")
