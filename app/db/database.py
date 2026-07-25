from collections.abc import Generator

from psycopg2 import pool
from psycopg2.extensions import connection as PgConnection
from psycopg2.extras import RealDictCursor

from app.core.config import settings

# ThreadedConnectionPool (não SimpleConnectionPool) — o servidor ASGI despacha pedidos
# em threads diferentes; SimpleConnectionPool diz explicitamente na sua docstring que
# "can't be shared across different threads".
_pool = pool.ThreadedConnectionPool(
    minconn=1,
    maxconn=10,
    host=settings.DB_HOST,
    port=settings.DB_PORT,
    dbname=settings.DB_NAME,
    user=settings.DB_USER,
    password=settings.DB_PASSWORD,
)


def get_connection() -> PgConnection:
    return _pool.getconn()


def release_connection(conn: PgConnection) -> None:
    _pool.putconn(conn)


def get_db() -> Generator[RealDictCursor]:
    """Dependência FastAPI: entrega um cursor (RealDictCursor) já aberto, comita se a rota
    terminar sem excepção, faz rollback e relança se não terminar (o rollback fica
    explícito aqui — antes disto já acontecia de forma implícita, mas só quando a ligação
    voltava à pool via putconn(), o que psycopg2.pool já garante para transacções por
    terminar; ver analise-tesouraria-historico.md, secção "Fiabilidade/Concorrência"). Substitui o
    bloco `conn = get_connection(); cursor = ...; try/finally` repetido em cada endpoint.

    Um serviço que precise da ligação em si (para comitar/reverter a meio, ex.
    guardar_em_cache ou uma UniqueViolation) usa `cursor.connection` — não há necessidade
    de passar `conn` à parte."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        yield cursor
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cursor.close()
        release_connection(conn)