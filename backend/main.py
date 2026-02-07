from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Depends, Header, Request
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
import requests

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
                   TEXT,
                   q3
                   INTEGER,
                   q4
                   INTEGER,
                   q5
                   INTEGER,
                   q6
                   INTEGER,
                   q7
                   INTEGER,
                   q8
                   INTEGER,
                   q9
                   INTEGER,
                   q10
                   INTEGER,
                   q11
                   INTEGER,
                   q12
                   INTEGER,
                   q13
                   INTEGER,
                   q14
                   INTEGER,
                   q15
                   INTEGER,
                   q16
                   INTEGER,
                   q17
                   INTEGER
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


# Answer mapping: Maps question text answers to integer values (1-4)
ANSWER_MAPPINGS = {
    "Quel est ton style de musique préféré ?": {
        "Rap": 1,
        "Pop": 2,
        "Rock": 3,
        "Autre": 4,
    },
    "Quel est pour toi le voyage idéal ?": {
        "Voyage en famille": 1,
        "Voyage entre amis": 2,
        "Voyage en couple": 3,
        "Voyage solo": 4,
    },
    "Quelle est ta destination de rêve ?": {
        "Londres": 1,
        "Séoul": 2,
        "Marrakech": 3,
        "Rio de Janeiro": 4,
    },
    "Quel est ton genre de film/série préféré ?": {
        "Science-Fiction": 1,
        "Drame": 2,
        "Comédie": 3,
        "Action": 4,
    },
    "Tu passes le plus de temps sur :": {
        "Instagram": 1,
        "Snapchat": 2,
        "TikTok": 3,
        "Je ne suis pas vraiment sur les réseaux": 4,
    },
    "A l'école tu préfères :": {
        "Histoire-Géographie": 1,
        "Anglais": 2,
        "Sport": 3,
        "Français/Philosophie": 4,
    },
    "Au petit-déjeuner c'est plutôt :": {
        "Café/Thé": 1,
        "Jus de fruit": 2,
        "Eau": 3,
        "Soda": 4,
    },
    "Au petit-déjeuner c'est plutôt :\xa0": {  # With non-breaking space
        "Café/Thé": 1,
        "Jus de fruit": 2,
        "Eau": 3,
        "Soda": 4,
    },
    "A Passy, le midi tu préfères être :": {
        "Dehors": 1,
        "Dans l'atrium": 2,
        "Dans la cour": 3,
        "En salle Verte/Bleue": 4,
    },
    "Avec 1.000.000 d'euros tu ferais plutôt :": {
        "Un don à un association": 1,
        "L'achat d'une maison dans le Sud": 2,
        "Un investissement boursier": 3,
        "Du shopping sur les Champs": 4,
    },
    "Comme super pouvoir, tu préfèrerais pouvoir :": {
        "Voler": 1,
        "Etre invisible": 2,
        "Lire dans les pensée": 3,
        "Remonter le temps": 4,
    },
    "Quelle est ta saison préférée :": {
        "Été": 1,
        "Automne": 2,
        "Hiver": 3,
        "Printemps": 4,
    },
    "Tu préfères lire :": {
        "Des romans": 1,
        "Des BD/mangas": 2,
        "Les journaux": 3,
        "Lire ?": 4,
    },
    "Tu préfères pratiquer quel sport :": {
        "Sport de raquette": 1,
        "Sport collectif": 2,
        "Sport de performance (athlétisme, natation...)": 3,
        "Sport de combat": 4,
    },
    "Tu préfères pratiquer quel sport :\xa0": {  # With non-breaking space
        "Sport de raquette": 1,
        "Sport collectif": 2,
        "Sport de performance (athlétisme, natation...)": 3,
        "Sport de combat": 4,
    },
    "Quelle est ta soirée idéale ?": {
        "Soirée cinéma": 1,
        "Soirée entre amis": 2,
        "Soirée dodo": 3,
        "Soirée gaming": 4,
    },
    "Si tu pouvais dîner avec une personne historique ce serait :": {
        "Michael Jackson": 1,
        "Jules César": 2,
        "Pelé": 3,
        "Pythagore (même si t'as oublié son théorème)": 4,
    },
}

# Map question text to column names
QUESTION_TO_COLUMN = {
    "Quel est ton style de musique préféré ?": "q3",
    "Quel est pour toi le voyage idéal ?": "q4",
    "Quelle est ta destination de rêve ?": "q5",
    "Quel est ton genre de film/série préféré ?": "q6",
    "Tu passes le plus de temps sur :": "q7",
    "A l'école tu préfères :": "q8",
    "Au petit-déjeuner c'est plutôt :": "q9",
    "Au petit-déjeuner c'est plutôt :\xa0": "q9",  # With non-breaking space
    "A Passy, le midi tu préfères être :": "q10",
    "Avec 1.000.000 d'euros tu ferais plutôt :": "q11",
    "Comme super pouvoir, tu préfèrerais pouvoir :": "q12",
    "Quelle est ta saison préférée :": "q13",
    "Tu préfères lire :": "q14",
    "Tu préfères pratiquer quel sport :": "q15",
    "Tu préfères pratiquer quel sport :\xa0": "q15",  # With non-breaking space
    "Quelle est ta soirée idéale ?": "q16",
    "Si tu pouvais dîner avec une personne historique ce serait :": "q17",
}


def parse_answer(question: str, answer: str) -> int | None:
    """Parse a text answer and convert it to integer (1-4).

    Args:
        question: The question text
        answer: The answer text

    Returns:
        Integer value (1-4) or None if answer cannot be mapped
    """
    if not answer or pd.isna(answer):
        return None

    # Clean up the answer (remove extra spaces, normalize)
    answer = str(answer).strip()

    # Normalize the question (remove non-breaking spaces, extra spaces)
    question_normalized = question.replace('\xa0', ' ').replace('  ', ' ').strip()

    # Try to find the mapping for this question (try variations)
    mapping = None
    for q_key in ANSWER_MAPPINGS.keys():
        q_key_normalized = q_key.replace('\xa0', ' ').replace('  ', ' ').strip()
        if q_key_normalized == question_normalized or q_key == question:
            mapping = ANSWER_MAPPINGS[q_key]
            break

    if mapping is None:
        return None

    # Try exact match first
    if answer in mapping:
        return mapping[answer]

    # Try case-insensitive match
    for key, value in mapping.items():
        if key.lower() == answer.lower():
            return value

    # Try partial match (for typos or extra spaces)
    for key, value in mapping.items():
        if key.lower() in answer.lower() or answer.lower() in key.lower():
            return value

    logging.warning(f"Could not map answer '{answer}' for question '{question}'")
    return None


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


def import_xlsx_df(df_raw: pd.DataFrame, passwd_len: int = 8) -> dict:
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
            raw_name = df_raw.at[idx, "Name"] if "Name" in df_raw.columns else None
            name = parse_name(raw_name)

            user_id = int(row["ID"]) if pd.notna(row.get("ID")) else None
            first_name = name.get("first_name")
            last_name = name.get("last_name")
            email = row.get("Email")

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

            # Parse answers for questions 3-17 and convert to integers
            parsed_answers = {}
            for question_text, column_name in QUESTION_TO_COLUMN.items():
                # Try to find the question in the answers dict (with possible variations)
                answer_text = answers.get(question_text)
                if answer_text is None:
                    # Try variations with spaces/special chars
                    for key in answers.keys():
                        if key and question_text.replace(" ", "").lower() == key.replace(" ", "").lower():
                            answer_text = answers[key]
                            break

                # Convert text answer to integer
                if answer_text:
                    parsed_value = parse_answer(question_text, answer_text)
                    if parsed_value is not None:
                        parsed_answers[column_name] = parsed_value
                    else:
                        logging.warning(
                            f"Could not parse answer for user {user_id}, question: {question_text}, answer: {answer_text}")

            # Insert or update user with basic info
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

            # Update user with parsed answers if we have any
            if parsed_answers:
                # Build dynamic UPDATE query for available answers
                set_clauses = []
                values = []
                for col, val in parsed_answers.items():
                    set_clauses.append(f"{col} = %s")
                    values.append(val)

                if set_clauses:
                    values.append(str(user_id))
                    update_query = f"UPDATE users SET {', '.join(set_clauses)} WHERE id = %s"
                    cursor.execute(update_query, values)

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


@app.post("/import-xlsx")
async def import_xlsx(
        file: UploadFile,
        passwd_len: int = 8,
        request: Request,
        token: str = Form(...)
):
    expected_token = os.getenv("ADMIN_TOKEN")
    client_ip = request.client.host

    if not expected_token:
        raise HTTPException(500, "Configuration serveur manquante")

    # Comparaison sécurisée contre timing attacks
    if not secrets.compare_digest(token, expected_token):
        logging.warning(f"Tentative d'import avec mauvais token depuis {client_ip}")
        raise HTTPException(401, "Non autorisé")

    # Import autorisé
    try:
        contents = await file.read()
        df_raw = pd.read_excel(BytesIO(contents), dtype=object)
    except Exception as e:
        raise HTTPException(400, f"Erreur lecture XLSX: {e}")
    logging.info(f"Import autorisé depuis {client_ip}")
    result = import_xlsx_df(df_raw, passwd_len)
    return result


@app.post("/login")
def check_code(password: str = Form(...)):
    row = cursor.execute(
        "SELECT * FROM passwords WHERE password = %s",
        (password,)
    ).fetchone()

    if not row:
        raise HTTPException(403, "Code invalide")

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


@app.post("/createMatches")
def createMatches(request: Request,
        token: str = Form(...)):
    """Create matches based on answer similarity within the same level."""
    expected_token = os.getenv("ADMIN_TOKEN")
    client_ip = request.client.host

    if not expected_token:
        raise HTTPException(500, "Token expected")

        # Comparaison sécurisée contre timing attacks
    if not secrets.compare_digest(token, expected_token):
        logging.warning(f"Tentative de calcul des matchs avec mauvais token depuis {client_ip}")
        raise HTTPException(401, "Non autorisé")
    try:
        # Fetch all users with their answers from the users table directly
        cursor.execute("""
                       SELECT id,
                              first_name,
                              last_name,
                              currentClass,
                              q3,
                              q4,
                              q5,
                              q6,
                              q7,
                              q8,
                              q9,
                              q10,
                              q11,
                              q12,
                              q13,
                              q14,
                              q15,
                              q16,
                              q17
                       FROM users
                       WHERE q3 IS NOT NULL
                       """)
        rows = cursor.fetchall()

        if not rows:
            raise HTTPException(400, "No users with answers found")

        # Build a list of users with their data
        users = []
        for row in rows:
            user_id = row[0]
            first_name = row[1]
            last_name = row[2]
            current_class = row[3]
            # Create answers dict from q3-q17 columns
            answers = {
                'q3': row[4], 'q4': row[5], 'q5': row[6], 'q6': row[7], 'q7': row[8],
                'q8': row[9], 'q9': row[10], 'q10': row[11], 'q11': row[12], 'q12': row[13],
                'q13': row[14], 'q14': row[15], 'q15': row[16], 'q16': row[17], 'q17': row[18]
            }
            # Extract level from currentClass (e.g., "Terminale F" -> "Terminale")
            level = current_class.split()[0] if current_class and current_class.strip() else ""
            users.append({
                "id": user_id,
                "first_name": first_name,
                "last_name": last_name,
                "level": level,
                "answers": answers
            })

        # Group users by level
        users_by_level = {}
        for user in users:
            level = user["level"]
            if level not in users_by_level:
                users_by_level[level] = []
            users_by_level[level].append(user)

        # Clear existing matches
        cursor.execute("DELETE FROM matches")

        # Create matches for each level
        matches_created = 0
        for level, level_users in users_by_level.items():
            if not level_users:
                continue

            logging.info(f"Creating matches for level {level} with {len(level_users)} users")

            # Calculate compatibility scores between all pairs
            n = len(level_users)

            # Special case: exactly 3 users
            # For 3 users, we form a trio on both days but with different primary matches
            if n == 3:
                # For 3 users, arrange them in a circular pattern on each day
                # Day 1: 0→1, 1→2, 2→0
                # Day 2: 0→2, 2→1, 1→0 (reversed)
                # This ensures each person has a different match on each day
                day1_matches = {0: 1, 1: 2, 2: 0}
                day2_matches = {0: 2, 2: 1, 1: 0}

                logging.info(f"Special case - 3 users: circular matching day1=(0→1→2→0), day2=(0→2→1→0)")

                # Insert matches into database
                for idx, user in enumerate(level_users):
                    day1_id = level_users[day1_matches[idx]]["id"]
                    day2_id = level_users[day2_matches[idx]]["id"]

                    cursor.execute(
                        """INSERT INTO matches (id, day1, day2)
                           VALUES (%s, %s, %s) ON CONFLICT (id) DO
                           UPDATE
                           SET day1 = EXCLUDED.day1, day2 = EXCLUDED.day2""",
                        (user["id"], day1_id, day2_id)
                    )
                    matches_created += 1

                continue  # Skip to next level

            scores = {}
            for i in range(n):
                for j in range(i + 1, n):
                    user_a = level_users[i]
                    user_b = level_users[j]
                    compatibility = score(user_a["answers"], user_b["answers"])
                    scores[(i, j)] = compatibility

            # Sort pairs by compatibility score (highest first)
            sorted_pairs = sorted(scores.items(), key=lambda x: x[1], reverse=True)

            # Create matches ensuring each person gets 2 different matches
            day1_matches = {}  # user_index -> matched_user_index
            day2_matches = {}
            day1_trio_members = set()  # Track who is in a trio on day 1

            # For day 1: greedy matching
            used = set()
            for (i, j), score_val in sorted_pairs:
                if i not in used and j not in used:
                    day1_matches[i] = j
                    day1_matches[j] = i
                    used.add(i)
                    used.add(j)

            # Handle odd number: create a group of 3 for day 1
            if len(used) < n:
                unmatched = [idx for idx in range(n) if idx not in used]
                if len(unmatched) == 1:
                    # Find an existing pair and add this person to form a trio
                    # The unmatched person will be matched with one person from a pair,
                    # creating an indirect trio relationship
                    if day1_matches:
                        # Find the best match for the unmatched person among those already matched
                        best_match_idx = None
                        best_score = -1
                        for idx in range(n):
                            if idx in used:
                                compatibility = score(level_users[unmatched[0]]["answers"], level_users[idx]["answers"])
                                if compatibility > best_score:
                                    best_score = compatibility
                                    best_match_idx = idx

                        if best_match_idx is not None:
                            day1_matches[unmatched[0]] = best_match_idx
                            used.add(unmatched[0])
                            partner = day1_matches.get(best_match_idx, "unknown")
                            # Mark all three people as being in a trio
                            day1_trio_members.add(unmatched[0])
                            day1_trio_members.add(best_match_idx)
                            day1_trio_members.add(partner)
                            logging.info(f"Formed trio on day 1: {unmatched[0]}, {best_match_idx}, {partner}")

            # For day 2: match differently, being strategic about who might end up in trios
            # If we had a trio on day 1 and will likely have one on day 2, try to ensure
            # different people are in the day 2 trio
            used2 = set()

            # If there was a day 1 trio and we expect a day 2 trio (odd number of users)
            # prioritize matching day 1 trio members first to avoid them being unmatched again
            if day1_trio_members and n % 2 == 1:
                # Sort pairs prioritizing matches involving day 1 trio members
                pairs_with_trio = []
                pairs_without_trio = []
                for (i, j), score_val in sorted_pairs:
                    if day1_matches.get(i) == j or day1_matches.get(j) == i:
                        continue
                    if i in day1_trio_members or j in day1_trio_members:
                        pairs_with_trio.append(((i, j), score_val))
                    else:
                        pairs_without_trio.append(((i, j), score_val))

                # Process trio members first
                for (i, j), score_val in pairs_with_trio:
                    if i not in used2 and j not in used2:
                        day2_matches[i] = j
                        day2_matches[j] = i
                        used2.add(i)
                        used2.add(j)

                # Then process others
                for (i, j), score_val in pairs_without_trio:
                    if i not in used2 and j not in used2:
                        day2_matches[i] = j
                        day2_matches[j] = i
                        used2.add(i)
                        used2.add(j)
            else:
                # Normal matching for day 2
                for (i, j), score_val in sorted_pairs:
                    if day1_matches.get(i) == j or day1_matches.get(j) == i:
                        continue
                    if i not in used2 and j not in used2:
                        day2_matches[i] = j
                        day2_matches[j] = i
                        used2.add(i)
                        used2.add(j)

            # Handle remaining unmatched for day 2
            unmatched2 = [idx for idx in range(n) if idx not in used2]
            if len(unmatched2) == 1:
                # Add to an existing pair to form a trio
                # IMPORTANT: Prefer matching with someone who was NOT in a trio on day 1
                if day2_matches:
                    # Find best match for unmatched person, avoiding day 1 trio members if possible
                    best_match_idx = None
                    best_score = -1
                    best_non_trio_match_idx = None
                    best_non_trio_score = -1

                    for idx in range(n):
                        if idx in used2:
                            score_val = score(level_users[unmatched2[0]]["answers"], level_users[idx]["answers"])
                            if score_val > best_score:
                                best_score = score_val
                                best_match_idx = idx
                            # Track best match among non-trio members from day 1
                            if idx not in day1_trio_members and score_val > best_non_trio_score:
                                best_non_trio_score = score_val
                                best_non_trio_match_idx = idx

                    # If unmatched person was in day 1 trio, prioritize matching with non-trio member
                    if unmatched2[0] in day1_trio_members and best_non_trio_match_idx is not None:
                        day2_matches[unmatched2[0]] = best_non_trio_match_idx
                        used2.add(unmatched2[0])
                        partner = day2_matches.get(best_non_trio_match_idx, "unknown")
                        logging.info(
                            f"Formed trio on day 2: {unmatched2[0]} (was in day1 trio) matched with {best_non_trio_match_idx} (was NOT in day1 trio), who is matched with {partner}")
                    elif best_match_idx is not None:
                        day2_matches[unmatched2[0]] = best_match_idx
                        used2.add(unmatched2[0])
                        partner = day2_matches.get(best_match_idx, "unknown")
                        logging.info(
                            f"Formed trio on day 2: {unmatched2[0]} matched with {best_match_idx}, who is matched with {partner}")
            elif len(unmatched2) == 2:
                # Match the remaining two
                day2_matches[unmatched2[0]] = unmatched2[1]
                day2_matches[unmatched2[1]] = unmatched2[0]
            elif len(unmatched2) == 3:
                # Create matches for three people - each gets one match
                # Form pairs with best compatibility among the three
                scores_trio = [
                    (0, 1, score(level_users[unmatched2[0]]["answers"], level_users[unmatched2[1]]["answers"])),
                    (0, 2, score(level_users[unmatched2[0]]["answers"], level_users[unmatched2[2]]["answers"])),
                    (1, 2, score(level_users[unmatched2[1]]["answers"], level_users[unmatched2[2]]["answers"]))
                ]
                scores_trio.sort(key=lambda x: x[2], reverse=True)
                # Use the best pair and match third person with one of them
                best_i, best_j, _ = scores_trio[0]
                day2_matches[unmatched2[best_i]] = unmatched2[best_j]
                day2_matches[unmatched2[best_j]] = unmatched2[best_i]
                # Match third person with one from the pair
                third = [x for x in [0, 1, 2] if x not in [best_i, best_j]][0]
                day2_matches[unmatched2[third]] = unmatched2[best_i]

            # Insert matches into database
            for idx, user in enumerate(level_users):
                day1_match_idx = day1_matches.get(idx)
                day2_match_idx = day2_matches.get(idx)

                day1_id = level_users[day1_match_idx]["id"] if day1_match_idx is not None else None
                day2_id = level_users[day2_match_idx]["id"] if day2_match_idx is not None else None

                cursor.execute(
                    """INSERT INTO matches (id, day1, day2)
                       VALUES (%s, %s, %s) ON CONFLICT (id) DO
                       UPDATE
                       SET day1 = EXCLUDED.day1, day2 = EXCLUDED.day2""",
                    (user["id"], day1_id, day2_id)
                )
                matches_created += 1

        db.commit()
        logging.info(f"Created {matches_created} matches")
        return {"created": matches_created}

    except Exception as e:
        logging.exception(f"Error creating matches: {e}")
        raise HTTPException(500, f"Error creating matches: {str(e)}")
