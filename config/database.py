"""
Data access layer for the dashboards.

Two backends, same public interface (``get_connection`` / ``run_query``):

* **SQLite** (``energy.db`` committed at the repo root) -- used on free hosting
  like Streamlit Community Cloud, which has no database server and a read-only
  filesystem.  This is the default whenever ``energy.db`` is present.
* **MySQL** -- the original local (XAMPP) backend, still used for development.
  Force it with ``DB_BACKEND=mysql``.

The SQLite connection is wrapped in a thin adapter that mimics the small slice
of the mysql-connector API the app relies on -- ``ping(reconnect=...)``,
``cursor(dictionary=True)`` and ``%s`` placeholders -- so ``core.auth`` and the
other modules keep working unchanged.

Every query is cached for 10 minutes, so the retry logic below matters: a
failed query inside a cached call would otherwise surface as a blank chart
rather than a message.
"""

import os
import sqlite3
import warnings
from pathlib import Path

import mysql.connector
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

# pandas emits a UserWarning for every read_sql() call made with a raw DBAPI2
# connection ("only supports SQLAlchemy connectable...").  The queries work
# fine, so suppress just that one warning -- otherwise it floods the Streamlit
# console on every cache miss and buries real errors.
warnings.filterwarnings(
    "ignore",
    message=".*only supports SQLAlchemy connectable.*",
    category=UserWarning,
)

ROOT = Path(__file__).resolve().parent.parent
SQLITE_PATH = ROOT / "energy.db"

# Backend selection: explicit DB_BACKEND wins; otherwise SQLite if the file is
# there, else MySQL.
BACKEND = os.getenv("DB_BACKEND", "").strip().lower()
if BACKEND not in ("sqlite", "mysql"):
    BACKEND = "sqlite" if SQLITE_PATH.exists() else "mysql"


class QueryError(RuntimeError):
    """Raised when a dashboard query cannot be run at all."""


def _db_config():
    return dict(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "energy_database_new"),
        port=int(os.getenv("DB_PORT", 3306)),
        connection_timeout=30,
        autocommit=True,
    )


# ---------------------------------------------------------------------------
# SQLite adapter -- exposes just enough of the mysql-connector surface
# ---------------------------------------------------------------------------
class _SQLiteCursor:
    def __init__(self, cur, dictionary):
        self._cur = cur
        self._dictionary = dictionary

    def execute(self, sql, params=None):
        # mysql-connector uses %s paramstyle; sqlite3 uses ?.
        self._cur.execute(sql.replace("%s", "?"), params or ())
        return self

    def _to_row(self, row):
        if row is None or not self._dictionary:
            return row
        cols = [d[0] for d in self._cur.description]
        return dict(zip(cols, row))

    def fetchone(self):
        return self._to_row(self._cur.fetchone())

    def fetchall(self):
        return [self._to_row(r) for r in self._cur.fetchall()]

    @property
    def description(self):
        return self._cur.description

    def close(self):
        self._cur.close()


class _SQLiteConnection:
    """Wraps a sqlite3 connection so it looks like a mysql-connector one."""

    def __init__(self, path):
        # check_same_thread=False: Streamlit runs widget callbacks on several
        # threads; the connection is only ever used for read queries.
        self.raw = sqlite3.connect(str(path), check_same_thread=False)

    def ping(self, *args, **kwargs):
        # No-op reconnect guard kept for API parity with mysql-connector.
        self.raw.execute("SELECT 1").fetchone()

    def cursor(self, dictionary=False):
        return _SQLiteCursor(self.raw.cursor(), dictionary)

    def close(self):
        self.raw.close()


def _connect():
    if BACKEND == "sqlite":
        return _SQLiteConnection(SQLITE_PATH)
    return mysql.connector.connect(**_db_config())


def _pandas_conn(conn):
    """pandas special-cases a real sqlite3.Connection, so unwrap it."""
    return getattr(conn, "raw", conn)


@st.cache_resource
def get_connection():
    return _connect()


def _live_connection():
    """Return a live connection, reconnecting automatically if stale."""
    conn = get_connection()
    try:
        conn.ping(reconnect=True, attempts=3, delay=1)
    except Exception:
        # Cache is stale — clear it and get a fresh connection
        get_connection.clear()
        conn = get_connection()
    return conn


# Which exception means "connection dropped, retry once" vs "query failed".
if BACKEND == "sqlite":
    _RETRY_ERRORS = (sqlite3.OperationalError, sqlite3.ProgrammingError)
    _QUERY_ERRORS = (sqlite3.Error,)
else:
    _RETRY_ERRORS = (mysql.connector.errors.OperationalError,)
    _QUERY_ERRORS = (mysql.connector.Error,)


@st.cache_data(ttl=600)
def run_query(query: str) -> pd.DataFrame:
    """Run one SQL query and return a DataFrame.

    Retries once on a dropped connection.  Any other failure is re-raised as
    QueryError so the calling page can show a useful message instead of
    rendering empty charts.
    """
    try:
        return pd.read_sql(query, _pandas_conn(_live_connection()))
    except _RETRY_ERRORS:
        # Force a brand-new connection and retry once
        get_connection.clear()
        try:
            return pd.read_sql(query, _pandas_conn(get_connection()))
        except Exception as exc:
            raise QueryError(f"Database unavailable: {exc}") from exc
    except _QUERY_ERRORS as exc:
        raise QueryError(f"Database error: {exc}") from exc
