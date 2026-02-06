import smtplib
import logging
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import psycopg
import asyncio
from concurrent.futures import ThreadPoolExecutor
import time

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

executor = ThreadPoolExecutor(max_workers=10)  # 10 at the same time (can go to 30)


def get_db_connection():
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        return psycopg.connect(database_url)

    return psycopg.connect(
        host=os.getenv('DB_HOST', 'localhost'),
        port=int(os.getenv('DB_PORT', '5432')),
        dbname=os.getenv('DB_NAME', 'saintvalentin'),
        user=os.getenv('DB_USER', 'postgres'),
        password=os.getenv('DB_PASSWORD', '')
    )


def send_email_blocking(destinataire: str, code: str) -> tuple:
    expediteur = os.getenv('EMAIL')
    mot_de_passe = os.getenv('PASSWORD')

    if not expediteur or not mot_de_passe:
        return (destinataire, False, "Config email manquante")

    message = MIMEMultipart()
    message["From"] = expediteur
    message["To"] = destinataire
    message["Subject"] = "🎀 Ton code d'accès - Saint Valentin Event"

    corps = f"Voici ton code d'accès : {code}\n\nUtilise ce code pour t'identifier sur la plateforme."
    message.attach(MIMEText(corps, "plain"))

    try:
        # Connexion SMTP
        server = smtplib.SMTP("smtp.office365.com", 587, timeout=10)
        server.starttls()
        server.login(expediteur, mot_de_passe)
        server.send_message(message)
        server.quit()
        return (destinataire, True, "OK")

    except smtplib.SMTPAuthenticationError:
        return (destinataire, False, "Auth error")
    except smtplib.SMTPException as e:
        return (destinataire, False, f"SMTP: {str(e)[:30]}")
    except Exception as e:
        return (destinataire, False, f"Error: {str(e)[:30]}")


async def send_all_emails_async():
    db = None
    cursor = None

    try:
        start_time = time.time()
        logger.info("Lauching ...")

        # Get data
        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute(
            """SELECT users.email, passwords.password, users.first_name
               FROM users
                        JOIN passwords ON users.id = passwords.user_id::TEXT
               ORDER BY users.first_name"""
        )
        rows = cursor.fetchall()

        if not rows:
            logger.warning("⚠️ Aucun utilisateur trouvé")
            return

        cursor.close()
        db.close()

        logger.info(f"📧 {len(rows)} emails à envoyer\n")

        # Send all mails at the same time
        loop = asyncio.get_event_loop()
        tasks = []

        for email, code, first_name in rows:
            task = loop.run_in_executor(executor, send_email_blocking, email, code)
            tasks.append(task)

        # Waiting for results
        results = await asyncio.gather(*tasks)

        success = sum(1 for _, ok, _ in results if ok)
        failed = len(results) - success

        errors = [(email, msg) for email, ok, msg in results if not ok]

        elapsed = time.time() - start_time

        logger.info(f"   Total : {len(results)}")
        logger.info(f"   Envoyés : {success}")
        logger.info(f"   Échoués : {failed}")
        logger.info(f"   Temps : {elapsed:.2f}s")
        logger.info(f"   Vitesse : {len(results) / elapsed:.0f} emails/sec")

        if errors:
            logger.warning(f"\n⚠️ Erreurs ({len(errors)}):")
            for email, msg in errors[:10]:
                logger.warning(f"   {email}: {msg}")
            if len(errors) > 10:
                logger.warning(f"   ... et {len(errors) - 10} autres")

    except Exception as e:
        logger.error(f"❌ Erreur : {str(e)}")
    finally:
        if cursor:
            try:
                cursor.close()
            except:
                pass
        if db:
            try:
                db.close()
            except:
                pass


if __name__ == "__main__":
    asyncio.run(send_all_emails_async())