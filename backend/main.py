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
import logging
from xlsxToJson import convert_xlsx_to_json


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


def generate_unique_password(length: int, cursor: sqlite3.Cursor) -> str:
    chars = string.ascii_lowercase + string.digits
    for _ in range(10000):
        code = ''.join(secrets.choice(chars) for _ in range(length))
        if cursor.execute("SELECT 1 FROM passwords WHERE password = ?", (code,)).fetchone():
            continue
        return code
    raise RuntimeError("Failed to generate a unique password after max attempts")

@app.post("/import")
def import_users_from_json(passwd_len: int = 6):
    convert_xlsx_to_json()
    #path = Path(json_path) if json_path else Path(__file__).resolve().parent / "input.json"
    path = Path(__file__).resolve().parent / 'input.json'
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {path}")

    cursor.execute("DELETE FROM passwords")
    cursor.execute("DELETE FROM users")
    db.commit()

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
    inserted = 0
    for u in users:
        id = u.get("id")

        first_name = u.get("first_name")
        last_name = u.get("last_name")
        email = u.get("email")
        currentClass = f"{u.get("answers")["Dans quel unité es-tu ?"]} {u.get("answers")["Dans quelle classe es-tu ?"]}"

        cursor.execute(
            "INSERT OR REPLACE INTO users (id, first_name, last_name, email, currentClass) VALUES (?, ?, ?, ?, ?)",
            (id, first_name, last_name, email, currentClass)
        )

        # try to generate and insert a unique password, handle rare race conditions
        try_count = 0
        while try_count < 5:
            code = generate_unique_password(passwd_len, cursor)
            try:
                cursor.execute(
                    "INSERT OR REPLACE INTO passwords (password, user_id) VALUES (?, ?)",
                    (code, id)
                )
                break
            except sqlite3.IntegrityError:
                try_count += 1
                continue
        else:
            # give up for this user after retries
            print(f"Failed to generate unique password for user {id}")
            continue

        inserted += 1

    db.commit()
    return {"imported": inserted, "password_length": passwd_len}
