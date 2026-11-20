"""
Database connections.

getdblocation() hands out a connection from a small shared pool instead of opening a new one for
every query. Opening a connection to the Render database (with SSL) takes a noticeable fraction of a
second, and one page or form submission runs several queries, so reusing connections is what keeps
the website responsive (UAT finding D-01: form submissions that seemed to hang).

Callers use the connection exactly as before: db.cursor(), db.commit(), db.rollback(), db.close().
close() returns the connection to the pool (any unfinished transaction is rolled back first).
"""
import os
import threading
import time

import pandas as pd
import psycopg2
from psycopg2 import pool as _pg_pool

POOL_MIN = 1
POOL_MAX = int(os.environ.get('DB_POOL_MAX', '10'))
CHECK_AFTER_IDLE_SECONDS = 30      # a connection idle longer than this is tested before it is reused

_pool = None
_pool_pid = None                   # a pool is never shared between gunicorn worker processes
_pool_lock = threading.Lock()
_last_used = {}                    # id(raw connection) -> time it was last returned to the pool


def _connect_kwargs():
    # Render sets DATABASE_URL in Environment Variables
    db_url = os.environ.get('DATABASE_URL')
    keepalive = dict(keepalives=1, keepalives_idle=30, keepalives_interval=10, keepalives_count=3,
                     connect_timeout=10)
    if db_url:
        # Production (Render)
        return dict(dsn=db_url, sslmode='require', **keepalive)
    # Local Development Fallback
    return dict(host='localhost', database='allura_db', user='postgres', port=5432, password='admin', **keepalive)


def _get_pool():
    global _pool, _pool_pid
    if _pool is None or _pool_pid != os.getpid():
        with _pool_lock:
            if _pool is None or _pool_pid != os.getpid():
                _pool = _pg_pool.ThreadedConnectionPool(POOL_MIN, POOL_MAX, **_connect_kwargs())
                _pool_pid = os.getpid()
    return _pool


class PooledConnection:
    """Wraps a psycopg2 connection so close() gives it back to the pool instead of closing it."""

    def __init__(self, raw, pooled=True):
        self._raw = raw
        self._pooled = pooled

    def __getattr__(self, name):            # cursor, commit, rollback, autocommit, ...
        return getattr(self._raw, name)

    def __setattr__(self, name, value):
        if name in ('_raw', '_pooled'):
            object.__setattr__(self, name, value)
        else:
            setattr(self._raw, name, value)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        if exc_type:
            try:
                self._raw.rollback()
            except Exception:
                pass
        self.close()

    def close(self):
        raw, self._raw = self._raw, None
        if raw is None:
            return
        if not self._pooled:
            try:
                raw.close()
            except Exception:
                pass
            return
        broken = bool(raw.closed)
        _last_used[id(raw)] = time.time()
        try:
            _get_pool().putconn(raw, close=broken)
        except Exception:
            try:
                raw.close()
            except Exception:
                pass

    def __del__(self):                      # a caller forgot to close (e.g. after an error)
        try:
            self.close()
        except Exception:
            pass


def _healthy(raw):
    if raw.closed:
        return False
    if time.time() - _last_used.get(id(raw), 0) < CHECK_AFTER_IDLE_SECONDS:
        return True
    try:
        cur = raw.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        raw.rollback()
        return True
    except Exception:
        return False


def getdblocation():
    """A database connection. Always call db.close() when done (it goes back to the pool)."""
    try:
        p = _get_pool()
        for _ in range(3):
            raw = p.getconn()
            if _healthy(raw):
                return PooledConnection(raw)
            p.putconn(raw, close=True)       # stale (e.g. the server dropped it while idle): replace it
    except _pg_pool.PoolError:
        pass                                 # every pooled connection is busy: use a one-off connection
    except psycopg2.OperationalError:
        raise
    return PooledConnection(psycopg2.connect(**_connect_kwargs()), pooled=False)


def modifyDB(sql, values):
    db = getdblocation()
    try:
        cursor = db.cursor()
        cursor.execute(sql, values)
        db.commit()
    finally:
        db.close()


def getDataFromDB(sql, values, dfcolumns):
    db = getdblocation()
    try:
        cur = db.cursor()
        cur.execute(sql, values)
        rows = pd.DataFrame(cur.fetchall(), columns=dfcolumns)
    finally:
        db.close()
    return rows
