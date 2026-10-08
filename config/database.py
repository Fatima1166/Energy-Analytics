"""
MySQL access layer for the dashboards.

Every query is cached for 10 minutes, so the warnings and the retry logic below
matter: a failed query inside a cached call would otherwise surface as a blank
chart rather than a message.
"""

import os
import warnings

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


@st.cache_resource
def get_connection():
    return mysql.connector.connect(**_db_config())


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


@st.cache_data(ttl=600)
def run_query(query: str) -> pd.DataFrame:
    """Run one SQL query and return a DataFrame.

    Retries once on a dropped connection.  Any other failure is re-raised as
    QueryError so the calling page can show a useful message instead of
    rendering empty charts.
    """
    try:
        return pd.read_sql(query, _live_connection())
    except mysql.connector.errors.OperationalError:
        # Force a brand-new connection and retry once
        get_connection.clear()
        try:
            return pd.read_sql(query, get_connection())
        except Exception as exc:
            raise QueryError(f"Database unavailable: {exc}") from exc
    except mysql.connector.Error as exc:
        raise QueryError(f"MySQL error: {exc}") from exc
