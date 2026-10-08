# generate_hash.py

import bcrypt
from db_core import get_connection

# ================== CONFIGURATION ==================
USERNAME  = "admin"
PASSWORD  = "energy@2026"
FULL_NAME = "Energy Administrator"
ROLE      = "admin"
# ===================================================


def main():
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(PASSWORD.encode("utf-8"), salt).decode("utf-8")

    print("=" * 60)
    print(f"USERNAME:  {USERNAME}")
    print(f"PASSWORD:  {PASSWORD}")
    print(f"HASH:      {hashed}")
    print("=" * 60)

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM dim_users WHERE username = %s", (USERNAME,))
        cursor.execute(
            """INSERT INTO dim_users (username, password_hash, full_name, role)
               VALUES (%s, %s, %s, %s)""",
            (USERNAME, hashed, FULL_NAME, ROLE),
        )
        conn.commit()
        print(f"\nUser '{USERNAME}' created successfully!")
        print(f"Login with: {USERNAME} / {PASSWORD}")
    except Exception as e:
        print(f"\nError: {e}")
    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    main()