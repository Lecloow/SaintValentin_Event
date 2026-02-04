# python
from pathlib import Path
import psycopg2
import json
import random
import string
from database import get_connection

def generate_password(length: int = 6) -> str:
    chars = string.ascii_lowercase + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

def import_users_from_json(json_path: str | None = None, passwd_len: int = 6):
    """
    Read JSON (list or dict) and import users into `users` table.
    For each user insert a generated unique password into `passwords`.
    Uses PostgreSQL database connection.
    """
    path = Path(json_path) if json_path else Path(__file__).resolve().parent / "input.json"
    if not path.exists():
        print(f"File not found: {path}")
        return

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # normalize to a list of user dicts
    if isinstance(data, dict):
        # common shapes: { "users": [...] } or single user object
        users = data.get("users") or data.get("data") or [data]
    elif isinstance(data, list):
        users = data
    else:
        print("Unsupported JSON format")
        return

    conn = get_connection()
    cursor = conn.cursor()

    try:
        inserted = 0
        for u in users:
            uid = u.get("id") or u.get("ID") or u.get("user_id") or u.get("uid")
            if not uid:
                # skip entries without id
                continue

            first_name = u.get("first_name") or u.get("firstName") or u.get("firstname") or ""
            last_name = u.get("last_name") or u.get("lastName") or u.get("lastname") or ""
            email = u.get("email") or ""
            currentClass = u.get("currentClass") or u.get("current_class") or ""

            # insert or replace user (keeps table consistent)
            cursor.execute(
                "INSERT INTO users (id, first_name, last_name, email, currentClass) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET first_name = EXCLUDED.first_name, last_name = EXCLUDED.last_name, email = EXCLUDED.email, currentClass = EXCLUDED.currentClass",
                (str(uid), first_name, last_name, email, currentClass)
            )

            # generate a unique password (avoid collisions with existing codes)
            for _ in range(100):  # retry up to 100 times
                code = generate_password(passwd_len)
                try:
                    cursor.execute(
                        "INSERT INTO passwords (password, user_id) VALUES (%s, %s)",
                        (code, str(uid))
                    )
                    break
                except psycopg2.IntegrityError:
                    # collision on password primary key; try again
                    conn.rollback()
                    continue
            else:
                # if no unique code found after retries, skip this user
                print(f"Failed to generate unique password for user {uid}")
                continue

            inserted += 1

        conn.commit()
        print(f"Imported {inserted} users and created passwords (length={passwd_len}).")
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    # default: read `input.json` located next to `backend/main.py`, generate 6\-char passwords
    import_users_from_json(None, passwd_len=6)
