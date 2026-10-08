import os
import sys
import mysql.connector
import pandas as pd
import bcrypt

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

DB_CONFIG = {
    "host": os.getenv("ENERGY_DB_HOST", "127.0.0.1"),
    "user": os.getenv("ENERGY_DB_USER", "root"),
    "password": os.getenv("ENERGY_DB_PASSWORD", ""),
    "database": os.getenv("ENERGY_DB_NAME", "energy_database_new"),
    "port": int(os.getenv("ENERGY_DB_PORT", "3306")),
}


class DatabaseConnectionError(Exception):
    """Raised when the analytics database cannot be reached."""


# ============================================================
# CONNECTION
# ============================================================
_connection = None


def get_connection():
    global _connection
    if _connection is None or not _connection.is_connected():
        _connection = mysql.connector.connect(**DB_CONFIG)
    return _connection


def run_query(query, params=None):
    conn = get_connection()
    return pd.read_sql(query, conn, params=params)


# ============================================================
# AUTHENTICATION
# ============================================================
def authenticate_user(username: str, password: str):
    query = """
        SELECT user_id, username, password_hash, full_name, role
        FROM dim_users
        WHERE username = %s
        LIMIT 1
    """
    try:
        df = run_query(query, params=(username,))
        if df.empty:
            return None
        row = df.iloc[0]
        stored_hash = row["password_hash"]
        if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
            return {
                "user_id":   int(row["user_id"]),
                "username":  row["username"],
                "full_name": row["full_name"],
                "role":      row["role"],
            }
        return None
    except Exception as e:
        raise DatabaseConnectionError(
            f"Could not connect to MySQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}. "
            "Start MySQL and verify the database settings."
        ) from e
