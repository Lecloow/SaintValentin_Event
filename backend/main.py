from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib3 import Path
import json
import datetime
import random
import string
import secrets
import smtplib
import ssl
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv
import pandas as pd
import sys
import psycopg
from io import BytesIO
import socket

load_dotenv()

logging.basicConfig(level=logging.INFO)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# PostgreSQL connection configuration
def get_db_connection():
    """Create and return a PostgreSQL database connection."""
    # Try to get DATABASE_URL first, otherwise construct from individual components
    database_url = os.getenv('DATABASE_URL')

    if database_url:
        # Parse DATABASE_URL if provided
        conn = psycopg.connect(database_url)
    else:
        # Construct connection from individual environment variables
        db_host = os.getenv('DB_HOST', 'localhost')
        db_port = os.getenv('DB_PORT', '5432')
        db_name = os.getenv('DB_NAME', 'saintvalentin')
        db_user = os.getenv('DB_USER', 'postgres')
        db_password = os.getenv('DB_PASSWORD', '')

        conn = psycopg.connect(
            host=db_host,
            port=db_port,
            dbname=db_name,
            user=db_user,
            password=db_password
        )

    return conn


# Initialize database connection
# Note: This uses a single connection for simplicity. For production use with high concurrency,
# consider implementing connection pooling (e.g., psycopg.pool) or using dependency injection
# to create connections per request.
db = get_db_connection()
cursor = db.cursor()

cursor.execute("""
               CREATE TABLE IF NOT EXISTS passwords
               (
                   password
                   TEXT
                   PRIMARY
                   KEY,
                   user_id
                   INTEGER
               )
               """)

cursor.execute("""
               CREATE TABLE IF NOT EXISTS users
               (
                   id
                   TEXT
                   PRIMARY
                   KEY,
                   first_name
                   TEXT,
                   last_name
                   TEXT,
                   email
                   TEXT,
                   currentClass
                   TEXT
               )
               """)

cursor.execute("""
               CREATE TABLE IF NOT EXISTS matches
               (
                   id
                   TEXT
                   PRIMARY
                   KEY,
                   day1
                   TEXT,
                   day2
                   TEXT,
                   day3
                   TEXT
               )
               """)

db.commit()


# Add shutdown event to close database connection
@app.on_event("shutdown")
def shutdown_event():
    """Close database connection on application shutdown."""
    try:
        if cursor is not None:
            cursor.close()
    except Exception as e:
        logging.error(f"Error closing cursor: {e}")

    try:
        if db is not None:
            db.close()
    except Exception as e:
        logging.error(f"Error closing database connection: {e}")


# --------------------
# MODELS
# --------------------
class CodePayload(BaseModel):
    password: str
    # user_id: str


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


def parse_name(full_name: str) -> dict:
    if not full_name or pd.isna(full_name):
        return {"first_name": "", "last_name": ""}

    parts = full_name.strip().split()

    # Trouver où commence le nom (les parties en MAJUSCULES)
    last_name_parts = []
    first_name_parts = []

    # On parcourt depuis la fin pour catcher le nom en majuscules
    i = len(parts) - 1
    while i >= 0 and parts[i].isupper():
        last_name_parts.insert(0, parts[i])
        i -= 1

    # Le reste c'est le prénom
    first_name_parts = parts[: i + 1]

    first_name = " ".join(first_name_parts).strip()
    # Capitaliser proprement le nom
    last_name = " ".join(p.capitalize() for p in last_name_parts).strip()

    # Si on a rien trouvé en majuscules, on fait un split simple (moitié/moitié)
    if not last_name and len(parts) >= 2:
        first_name = parts[0]
        last_name = " ".join(parts[1:]).capitalize()
    elif not first_name and last_name:
        # Tout était en majuscules, on garde juste le dernier comme nom
        first_name = " ".join(last_name_parts[:-1])
        last_name = last_name_parts[-1].capitalize() if last_name_parts else ""

    return {"first_name": first_name, "last_name": last_name}


def import_xlsx_df(df_raw: pd.DataFrame, passwd_len: int = 6) -> dict:
    """Import a DataFrame (read from XLSX) directly into the PostgreSQL DB.

    - df_raw: raw DataFrame loaded from the original XLSX (keeps the "Nom" column if present)
    - passwd_len: length of generated passwords

    Returns: dict with keys {imported, password_length}
    """
    # Work on a copy and drop unwanted columns (same logic as before)
    df = df_raw.copy()

    drop_exact = [
        "Heure de début",
        "Heure de fin",
        "Heure de la dernière modification",
        "Total points",
        "Quiz feedback",
        "Nom",
    ]
    drop_pattern = df.columns[
        df.columns.str.startswith("Points - ")
        | df.columns.str.startswith("Feedback - ")
        ].tolist()
    all_to_drop = drop_exact + drop_pattern
    df = df.drop(columns=[c for c in all_to_drop if c in df.columns])

    # Clear existing tables
    cursor.execute("DELETE FROM passwords")
    cursor.execute("DELETE FROM users")
    db.commit()

    inserted = 0

    for idx, row in df.iterrows():
        try:
            raw_name = df_raw.at[idx, "Nom"] if "Nom" in df_raw.columns else None
            name = parse_name(raw_name)

            user_id = int(row["ID"]) if pd.notna(row.get("ID")) else None
            first_name = name.get("first_name") or row.get("Prenom") or ""
            last_name = name.get("last_name") or row.get("Nom") or ""
            email = row.get("Adresse de messagerie") or row.get("Email") or row.get("email") or ""

            # Build answers dict from remaining columns
            skip_cols = ["ID", "Adresse de messagerie"]
            answers = {}
            for col in df.columns:
                if col not in skip_cols:
                    value = row[col]
                    clean_col = str(col).replace("\xa0", " ").strip()
                    answers[clean_col] = str(value) if pd.notna(value) else None

            # Try to construct currentClass from answers if possible
            unit = answers.get("Dans quel unité es-tu ?") or answers.get("Dans quelle unité es-tu ?") or ""
            classe = answers.get("Dans quelle classe es-tu ?") or answers.get("Dans quelle classe es-tu ?") or ""
            currentClass = f"{unit} {classe}".strip()

            cursor.execute(
                """INSERT INTO users (id, first_name, last_name, email, currentClass)
                   VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO
                UPDATE SET
                    first_name = EXCLUDED.first_name,
                    last_name = EXCLUDED.last_name,
                    email = EXCLUDED.email,
                    currentClass = EXCLUDED.currentClass""",
                (str(user_id), first_name, last_name, email, currentClass)
            )

            # generate and insert a unique password
            try_count = 0
            while try_count < 5:
                code = generate_unique_password(passwd_len, cursor)
                try:
                    cursor.execute(
                        """INSERT INTO passwords (password, user_id)
                           VALUES (%s, %s) ON CONFLICT (password) DO NOTHING""",
                        (code, user_id)
                    )
                    # Check if the insert was successful
                    if cursor.rowcount > 0:
                        break
                    # If rowcount is 0, there was a conflict, try again
                except psycopg.IntegrityError:
                    try_count += 1
                    continue
            else:
                logging.warning(f"Failed to generate unique password for user {user_id}")
                continue

            inserted += 1
        except Exception as e:
            logging.exception(f"Skipping row {idx} due to error: {e}")
            continue

    db.commit()
    return {"imported": inserted, "password_length": passwd_len}


# Refactor endpoint to use the reusable functions
@app.post("/import-xlsx")
async def import_xlsx(file: UploadFile, passwd_len: int = 6):
    """Importe un fichier XLSX (upload ou path) directement dans la base PostgreSQL sans créer de fichier JSON.

    This endpoint now simply reads the XLSX (either uploaded bytes or a path) and calls
    `import_xlsx_df` so the same logic can be used programmatically.
    """
    if file is None:
        raise HTTPException(status_code=400, detail="Provide either an uploaded file or a file_path")

    # Read DataFrame
    try:
        contents = await file.read()
        df_raw = pd.read_excel(BytesIO(contents), dtype=object)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read XLSX: {e}")

    result = import_xlsx_df(df_raw, passwd_len)
    return result


@app.post("/login")
def check_code(payload: CodePayload):
    row = cursor.execute(
        "SELECT * FROM passwords WHERE password = %s",
        (payload.password,)
    ).fetchone()

    if not row:
        raise HTTPException(403, "Code invalide")

    # return HTTPException(200, "user_id:", row[1])  # user_id
    user_id = row[1]
    user_row = cursor.execute(
        "SELECT id, first_name, last_name, email, currentClass FROM users WHERE id = %s",
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


def generate_unique_password(length: int, cursor) -> str:
    chars = string.ascii_lowercase + string.digits
    for _ in range(10000):
        code = ''.join(secrets.choice(chars) for _ in range(length))
        if cursor.execute("SELECT 1 FROM passwords WHERE password = %s", (code,)).fetchone():
            continue
        return code
    raise RuntimeError("Failed to generate a unique password after max attempts")


@app.post("/send-emails")
def sendEmails(destinataire: str, code: str):
    print("Launching sendEmails...")
    
    try:
        response = requests.post(
            f"https://api.mailgun.net/v3/{os.getenv('MAILGUN_DOMAIN')}/messages",
            auth=("api", os.getenv('MAILGUN_API_KEY')),
            data={
                "from": f"noreply@{os.getenv('MAILGUN_DOMAIN')}",
                "to": destinataire,
                "subject": "Code d'accès Saint-Valentin",
                "text": f"Ceci est ton code d'accès : {code}"
            }
        )
        
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            return {"status_code": 200, "message": "Email envoyé avec succès"}
        else:
            raise Exception(response.text)
    
    except Exception as e:
        print(f"❌ Erreur: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erreur : {str(e)}")


@app.post("/createMatches")
def createMatches():
    return {"created": 1}
