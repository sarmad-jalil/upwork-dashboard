import threading
from contextlib import contextmanager

import psycopg2
import psycopg2.extras
from psycopg2 import pool as pg_pool

from api.core.config import get_settings


class DatabaseNotConfiguredError(RuntimeError):
    pass


# Supabase may be several hundred ms away (this project's instance is in Tokyo),
# so a fresh connect per request cost ~1.5s in handshake alone. Reuse instead.
_pool = None
_pool_lock = threading.Lock()


def _get_pool():
    global _pool
    if _pool is not None:
        return _pool

    settings = get_settings()
    if not settings.database_url:
        raise DatabaseNotConfiguredError(
            "DATABASE_URL is not set. Add your Supabase Postgres connection string to backend/.env "
            "(Project Settings → Database → Connection string → URI)."
        )

    with _pool_lock:
        if _pool is None:
            _pool = pg_pool.ThreadedConnectionPool(
                minconn=1,
                maxconn=5,
                dsn=settings.database_url,
                cursor_factory=psycopg2.extras.RealDictCursor,
            )
    return _pool


@contextmanager
def get_conn():
    pool = _get_pool()
    conn = pool.getconn()
    broken = False
    try:
        yield conn
        conn.commit()
    except Exception:
        # A connection the server closed under us must not go back in the pool,
        # or the next caller inherits the failure.
        broken = True
        try:
            conn.rollback()
        except psycopg2.Error:
            pass
        raise
    finally:
        pool.putconn(conn, close=broken or conn.closed)
