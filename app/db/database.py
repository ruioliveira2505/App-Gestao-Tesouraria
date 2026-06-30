from psycopg2 import pool
from app.core.config import settings

_pool = pool.SimpleConnectionPool(
    minconn=1,
    maxconn=10,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    dbname=settings.DB_NAME,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
)


def get_connection():
    return _pool.getconn()


def release_connection(conn):
    _pool.putconn(conn)