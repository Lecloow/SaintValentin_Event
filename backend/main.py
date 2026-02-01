from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pathlib3 import Path
import sqlite3
import json
import datetime
import random
import string
import secrets
import os
import smtplib
import ssl
from email.message import EmailMessage
import logging


logging.basicConfig(level=logging.INFO)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


db = sqlite3.connect("data.db", check_same_thread=False)
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS passwords (
    password TEXT PRIMARY KEY,
    user_id INTEGER
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    email TEXT,
    currentClass TEXT
)
""")

db.commit()

# --------------------
# MODELS
# --------------------
class CodePayload(BaseModel):
    password: str
    #user_id: str

class AnswerPayload(BaseModel):
    code: str
    data: dict

class Person(BaseModel):
    id: str
    first_name: str
    last_name: str
    email: str
    currentClass: str


# --------------------
# UTILS
# --------------------

def score(a: dict, b: dict) -> int:
    s = 0
    for k in a:
        if k in b and a[k] == b[k]:
            s += 1
    return s

@app.post("/login")
def check_code(payload: CodePayload):
    row = cursor.execute(
        "SELECT * FROM passwords WHERE password = ?",
        (payload.password,)
    ).fetchone()

    if not row:
        raise HTTPException(403, "Code invalide")

    #return HTTPException(200, "user_id:", row[1])  # user_id
    user_id = row[1]
    user_row = cursor.execute(
        "SELECT id, first_name, last_name, email, currentClass FROM users WHERE id = ?",
        (str(user_id),),
    ).fetchone()

    if user_row:
        return {
            "id": user_row[0],
            "first_name": user_row[1],
            "last_name": user_row[2],
            "email": user_row[3],
            "currentClass": user_row[4],
        }

    return {"user_id": user_id}




# This is a test


def generate_unique_password(length: int, cursor: sqlite3.Cursor, seen: set, max_attempts: int = 10000) -> str:
    chars = string.ascii_lowercase + string.digits
    for _ in range(max_attempts):
        code = ''.join(secrets.choice(chars) for _ in range(length))
        if code in seen:
            continue
        if cursor.execute("SELECT 1 FROM passwords WHERE password = ?", (code,)).fetchone():
            continue
        seen.add(code)
        return code
    raise RuntimeError("Failed to generate a unique password after max attempts")

@app.post("/import")
def import_users_from_json(json_path: str | None = None, passwd_len: int = 6):
    path = Path(json_path) if json_path else Path(__file__).resolve().parent / "input.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    # normalize to a list of user dicts
    if isinstance(data, dict):
        users = data.get("users") or data.get("data") or [data]
    elif isinstance(data, list):
        users = data
    else:
        raise HTTPException(status_code=400, detail="Unsupported JSON format")

    # preload existing passwords to avoid duplicates during this run
    existing_passwords = set(row[0] for row in cursor.execute("SELECT password FROM passwords").fetchall())

    inserted = 0
    for u in users:
        uid = u.get("id") or u.get("ID") or u.get("user_id") or u.get("uid")
        if not uid:
            continue

        first_name = u.get("first_name")
        last_name = u.get("last_name")
        email = u.get("email")
        currentClass = f"{u.get("answers")["Dans quel unité es-tu ?"]} {u.get("answers")["Dans quelle classe es-tu ?"]}"

        cursor.execute(
            "INSERT OR REPLACE INTO users (id, first_name, last_name, email, currentClass) VALUES (?, ?, ?, ?, ?)",
            (str(uid), first_name, last_name, email, currentClass)
        )

        # try to generate and insert a unique password, handle rare race conditions
        try_count = 0
        while try_count < 5:
            code = generate_unique_password(passwd_len, cursor, existing_passwords)
            try:
                cursor.execute(
                    "INSERT INTO passwords (password, user_id) VALUES (?, ?)",
                    (code, str(uid))
                )
                break
            except sqlite3.IntegrityError:
                # concurrent insert may have used the same code; remove from seen and retry
                existing_passwords.discard(code)
                try_count += 1
                continue
        else:
            # give up for this user after retries
            print(f"Failed to generate unique password for user {uid}")
            continue

        inserted += 1

    db.commit()
    return {"imported": inserted, "password_length": passwd_len}

@app.post("/send-passwords-all")
def send_passwords_all():
    try:
        # SMTP configuration from environment
        smtp_host = os.getenv("SMTP_HOST")
        smtp_port = int(os.getenv("SMTP_PORT", "587"))
        smtp_user = os.getenv("SMTP_USER")
        smtp_pass = os.getenv("SMTP_PASS")
        smtp_from = os.getenv("SMTP_FROM", smtp_user)

        if not smtp_host or not smtp_user or not smtp_pass:
            raise HTTPException(status_code=500, detail="SMTP not configured (set SMTP_HOST/SMTP_USER/SMTP_PASS)")

        users = cursor.execute("SELECT id, first_name, last_name, email FROM users").fetchall()

        sent = 0
        skipped_no_email = 0
        skipped_no_password = 0
        errors = []

        context = ssl.create_default_context()

        try:
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_host, smtp_port, context=context)
            else:
                server = smtplib.SMTP(smtp_host, smtp_port)
                server.starttls(context=context)
            server.login(smtp_user, smtp_pass)
        except Exception as e:
            logging.exception("SMTP connection/login failed")
            raise HTTPException(status_code=500, detail=f"Failed to connect/login to SMTP server: {e}")

        with server:
            for u in users:
                uid, first_name, last_name, recipient_email = str(u[0]), u[1], u[2], u[3]
                if not recipient_email:
                    skipped_no_email += 1
                    continue

                pw_row = cursor.execute("SELECT password FROM passwords WHERE user_id = ? LIMIT 1", (uid,)).fetchone()
                if not pw_row:
                    skipped_no_password += 1
                    continue
                password = pw_row[0]

                msg = EmailMessage()
                msg["Subject"] = "Your access code"
                msg["From"] = smtp_from
                msg["To"] = recipient_email
                msg.set_content(
                    f"Hello {first_name} {last_name},\n\n"
                    f"Your access code is: {password}\n\n"
                    "Keep it safe.\n"
                )

                try:
                    server.send_message(msg)
                    sent += 1
                except Exception as e:
                    logging.exception("Failed to send message to %s", recipient_email)
                    errors.append({"user_id": uid, "email": recipient_email, "error": str(e)})
                    continue

        return {
            "sent": sent,
            "skipped_no_email": skipped_no_email,
            "skipped_no_password": skipped_no_password,
            "errors": errors,
        }

    except HTTPException:
        raise
    except Exception as e:
        logging.exception("Unhandled error in send_passwords_all")
        raise HTTPException(status_code=500, detail=str(e))