"""
Export the live MySQL energy database to a SQLite file for free hosting.

Streamlit Community Cloud has no database server and a read-only filesystem
(only /tmp is writable), so the whole dataset ships with the repo as a single
`energy.db` SQLite file.  This script reads every BASE TABLE from the local
MySQL instance (the source of truth -- the committed .sql dump is incomplete)
and writes it into SQLite.  Views are skipped because no dashboard query uses
them.

Usage:
    python -m scripts.export_sqlite
"""

import os
import sqlite3

import mysql.connector
import pandas as pd

# --- Source (local MySQL, same defaults as config/database.py) --------------
MYSQL = dict(
    host=os.getenv("DB_HOST", "127.0.0.1"),
    user=os.getenv("DB_USER", "root"),
    password=os.getenv("DB_PASSWORD", ""),
    database=os.getenv("DB_NAME", "energy_database_new"),
    port=int(os.getenv("DB_PORT", 3306)),
)

# --- Destination -----------------------------------------------------------
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_PATH = os.path.join(ROOT, "energy.db")


def base_tables(cur):
    cur.execute(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = %s AND table_type = 'BASE TABLE' "
        "ORDER BY table_name",
        (MYSQL["database"],),
    )
    return [r[0] for r in cur.fetchall()]


def main():
    if os.path.exists(OUT_PATH):
        os.remove(OUT_PATH)

    my = mysql.connector.connect(**MYSQL)
    lite = sqlite3.connect(OUT_PATH)
    try:
        cur = my.cursor()
        tables = base_tables(cur)
        cur.close()
        print(f"Found {len(tables)} base tables")

        total_rows = 0
        for t in tables:
            df = pd.read_sql(f"SELECT * FROM `{t}`", my)
            # sqlite3 is a special-cased DBAPI2 connection in pandas.to_sql.
            df.to_sql(t, lite, if_exists="replace", index=False)
            total_rows += len(df)
            print(f"  {t:38s} {len(df):6d} rows")

        lite.commit()
        print(f"\nWrote {len(tables)} tables, {total_rows} rows -> {OUT_PATH}")
    finally:
        lite.close()
        my.close()


if __name__ == "__main__":
    main()
