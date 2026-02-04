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
import psycopg2
from io import BytesIO
from database import get_connection, init_database

load_dotenv()

logging.basicConfig(level=logging.INFO)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database tables on startup
init_database()


def get_cursor():
    """Helper function to get a database connection and cursor"""
    conn = get_connection()
    cursor = conn.cursor()
    return conn, cursor


def close_connection(conn, cursor):
    """Helper function to close database connection and cursor"""
    if cursor:
        cursor.close()
    if conn:
        conn.close()

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


def convert_xlsx_to_json(input_path: str, output_path: str):
    # Lire le fichier Excel
    df = pd.read_excel(input_path)
    print(f"📋 {len(df)} entrées trouvées")

    # Colonnes à supprimer exactement
    drop_exact = [
        "Heure de début",
        "Heure de fin",
        "Heure de la dernière modification",
        "Total points",
        "Quiz feedback",
        "Nom",  # On la remplace par first_name + last_name
    ]

    # Supprimer les colonnes "Points - ..." et "Feedback - ..."
    drop_pattern = df.columns[
        df.columns.str.startswith("Points - ")
        | df.columns.str.startswith("Feedback - ")
    ].tolist()

    all_to_drop = drop_exact + drop_pattern
    df = df.drop(columns=[c for c in all_to_drop if c in df.columns])

    results = []

    for _, row in df.iterrows():
        # Séparer le nom
        name = parse_name(
            pd.read_excel(input_path)["Nom"].iloc[row.name]
        )

        entry = {
            "id": int(row["ID"]),
            "first_name": name["first_name"],
            "last_name": name["last_name"],
            "email": row["Adresse de messagerie"],
            "answers": {},
        }

        # Ajouter les réponses (tout ce qui reste sauf ID et email)
        skip_cols = ["ID", "Adresse de messagerie"]
        for col in df.columns:
            if col not in skip_cols:
                value = row[col]
                # Nettoyer les \xa0 (espace insécable) dans les clés
                clean_col = col.replace("\xa0", " ").strip()
                entry["answers"][clean_col] = (
                    str(value) if pd.notna(value) else None
                )

        results.append(entry)

    # --- Écrire le JSON ---
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


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

    conn, cursor = get_cursor()
    
    try:
        # Clear existing tables
        cursor.execute("DELETE FROM passwords")
        cursor.execute("DELETE FROM users")
        conn.commit()

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
                    "INSERT INTO users (id, first_name, last_name, email, currentClass) VALUES (%s, %s, %s, %s, %s) ON CONFLICT (id) DO UPDATE SET first_name = EXCLUDED.first_name, last_name = EXCLUDED.last_name, email = EXCLUDED.email, currentClass = EXCLUDED.currentClass",
                    (str(user_id), first_name, last_name, email, currentClass)
                )

                # generate and insert a unique password
                try_count = 0
                while try_count < 5:
                    code = generate_unique_password(passwd_len, cursor)
                    try:
                        cursor.execute(
                            "INSERT INTO passwords (password, user_id) VALUES (%s, %s) ON CONFLICT (password) DO UPDATE SET user_id = EXCLUDED.user_id",
                            (code, user_id)
                        )
                        break
                    except psycopg2.IntegrityError:
                        try_count += 1
                        conn.rollback()
                        continue
                else:
                    logging.warning(f"Failed to generate unique password for user {user_id}")
                    continue

                inserted += 1
            except Exception as e:
                logging.exception(f"Skipping row {idx} due to error: {e}")
                conn.rollback()
                continue

        conn.commit()
        return {"imported": inserted, "password_length": passwd_len}
    finally:
        close_connection(conn, cursor)


def import_xlsx_from_path(file_path: str, passwd_len: int = 6) -> dict:
    """Helper to read an XLSX from disk and import it into DB (calls import_xlsx_df)."""
    p = Path(file_path)
    if not p.exists():
        raise FileNotFoundError(file_path)
    df_raw = pd.read_excel(p, dtype=object)
    return import_xlsx_df(df_raw, passwd_len)


# Refactor endpoint to use the reusable functions
@app.post("/import-xlsx")
async def import_xlsx(file: UploadFile | None = File(None), file_path: str | None = None, passwd_len: int = 6):
    """Importe un fichier XLSX (upload ou path) directement dans la base SQLite sans créer de fichier JSON.

    This endpoint now simply reads the XLSX (either uploaded bytes or a path) and calls
    `import_xlsx_df` so the same logic can be used programmatically.
    """
    if file is None and file_path is None:
        raise HTTPException(status_code=400, detail="Provide either an uploaded file or a file_path")

    # Read DataFrame
    try:
        if file is not None:
            contents = await file.read()
            df_raw = pd.read_excel(BytesIO(contents), dtype=object)
        else:
            df_raw = pd.read_excel(Path(file_path), dtype=object)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read XLSX: {e}")

    result = import_xlsx_df(df_raw, passwd_len)
    return result


@app.get("/download-db/")
async def download_db():
    """Download database is not available for PostgreSQL"""
    raise HTTPException(status_code=501, detail="Database download not supported for PostgreSQL")


@app.post("/login")
def check_code(payload: CodePayload):
    conn, cursor = get_cursor()
    
    try:
        cursor.execute(
            "SELECT * FROM passwords WHERE password = %s",
            (payload.password,)
        )
        row = cursor.fetchone()

        if not row:
            raise HTTPException(403, "Code invalide")

        #return HTTPException(200, "user_id:", row[1])  # user_id
        user_id = row[1]
        cursor.execute(
            "SELECT id, first_name, last_name, email, currentClass FROM users WHERE id = %s",
            (str(user_id),),
        )
        user_row = cursor.fetchone()

        if user_row:
            return {
                "id": user_row[0],
                "first_name": user_row[1],
                "last_name": user_row[2],
                "email": user_row[3],
                "currentClass": user_row[4],
            }

        return {"user_id": user_id}
    finally:
        close_connection(conn, cursor)


def generate_unique_password(length: int, cursor) -> str:
    chars = string.ascii_lowercase + string.digits
    for _ in range(10000):
        code = ''.join(secrets.choice(chars) for _ in range(length))
        cursor.execute("SELECT 1 FROM passwords WHERE password = %s", (code,))
        if cursor.fetchone():
            continue
        return code
    raise RuntimeError("Failed to generate a unique password after max attempts")

@app.post("/send-emails")
def sendEmails(destinataire: str, code: str):
    print("Launching sendEmails...")
    expediteur = os.getenv('EMAIL')
    mot_de_passe = os.getenv('PASSWORD')
    destinataire = destinataire

    smtp_server = "smtp.office365.com"
    port = 587
    print("trying to connect")

    message = MIMEMultipart()
    message["From"] = expediteur
    message["To"] = destinataire
    message["Subject"] = "Test email"

    corps = f"Ceci est ton code d'accès : {code}"
    message.attach(MIMEText(corps, "plain"))

    server = None
    try:
        server = smtplib.SMTP(smtp_server, port)
        server.starttls()  # Sécuriser la connexion
        server.login(expediteur, mot_de_passe)
        server.send_message(message)
        server.quit()
        return {"status_code": 200, "message": "Email envoyé avec succès"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erreur inconnue : {str(e)}"
        )

    finally:
        if server:
            try:
                server.quit()
            except:
                pass
@app.post("/createMatches")
def createMatches():
    return {"created": 1}