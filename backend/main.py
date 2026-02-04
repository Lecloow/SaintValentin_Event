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

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Variables globales pour la connexion
_db = None
_cursor = None


def get_db_connection():
    """Create and return a PostgreSQL database connection."""
    global _db, _cursor

    if _db is not None:
        return _db

    try:
        # Try to get DATABASE_URL first
        database_url = os.getenv('DATABASE_URL')

        if database_url:
            _db = psycopg.connect(database_url)
        else:
            # Construct connection from individual environment variables
            db_host = os.getenv('DB_HOST', 'localhost')
            db_port = os.getenv('DB_PORT', '5432')
            db_name = os.getenv('DB_NAME', 'saintvalentin')
            db_user = os.getenv('DB_USER', 'postgres')
            db_password = os.getenv('DB_PASSWORD', '')

            _db = psycopg.connect(
                host=db_host,
                port=db_port,
                dbname=db_name,
                user=db_user,
                password=db_password
            )

        _cursor = _db.cursor()
        logger.info("✅ Database connection established")
        return _db
    except Exception as e:
        logger.error(f"❌ Database connection failed: {e}")
        _db = None
        _cursor = None
        raise


def init_tables():
    """Initialize database tables."""
    try:
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
        logger.info("✅ Tables initialized")
    except Exception as e:
        logger.error(f"❌ Table initialization failed: {e}")


# Initialize tables on startup
@app.on_event("startup")
def startup_event():
    """Initialize database on app startup."""
    try:
        init_tables()
    except Exception as e:
        logger.error(f"Startup error: {e}")


# Shutdown event
@app.on_event("shutdown")
def shutdown_event():
    """Close database connection on application shutdown."""
    global _db, _cursor
    try:
        if _cursor is not None:
            _cursor.close()
    except Exception as e:
        logger.error(f"Error closing cursor: {e}")

    try:
        if _db is not None:
            _db.close()
    except Exception as e:
        logger.error(f"Error closing database connection: {e}")

    _db = None
    _cursor = None


# --------------------
# MODELS
# --------------------
class CodePayload(BaseModel):
    password: str


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


# --------------------
# ROUTES
# --------------------

@app.get("/")
def read_root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Backend is running"}


@app.get("/health")
def health_check():
    """Health check endpoint with database status."""
    try:
        db = get_db_connection()
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


@app.post("/login")
def login(payload: CodePayload):
    """Login endpoint."""
    try:
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            "SELECT user_id FROM passwords WHERE password = %s",
            (payload.password,)
        )
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=401, detail="Invalid password")

        user_id = result[0]
        cursor.execute(
            "SELECT id, first_name, last_name, email, currentClass FROM users WHERE id = %s",
            (user_id,)
        )
        user = cursor.fetchone()

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return {
            "id": user[0],
            "first_name": user[1],
            "last_name": user[2],
            "email": user[3],
            "currentClass": user[4]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@app.post("/submit")
def submit_answers(payload: AnswerPayload):
    """Submit quiz answers."""
    try:
        db = get_db_connection()
        cursor = db.cursor()

        # Find the user by password
        cursor.execute(
            "SELECT user_id FROM passwords WHERE password = %s",
            (payload.code,)
        )
        result = cursor.fetchone()

        if not result:
            raise HTTPException(status_code=401, detail="Invalid code")

        user_id = result[0]

        # Store the answers (implementation depends on your schema)
        logger.info(f"Answers received from user {user_id}")

        return {"status": "success", "message": "Answers submitted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Submit error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")