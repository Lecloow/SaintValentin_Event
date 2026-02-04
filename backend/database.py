"""
PostgreSQL Database Management Module
Handles database connection, table creation, and transaction management for the Saint Valentin Event application.
"""
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_database_url():
    """Get the database URL from environment variable or use a default for local development"""
    return os.getenv('DATABASE_URL', 'postgresql://localhost/saintvalentin')


def get_connection():
    """Create and return a new database connection"""
    database_url = get_database_url()
    try:
        conn = psycopg2.connect(database_url)
        return conn
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        raise


@contextmanager
def get_cursor(commit=True):
    """
    Context manager for database operations
    
    Args:
        commit: If True, commits the transaction on success
        
    Usage:
        with get_cursor() as cursor:
            cursor.execute("SELECT * FROM users")
            results = cursor.fetchall()
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"Database operation failed: {e}")
        raise
    finally:
        cursor.close()
        conn.close()


def create_tables():
    """Create all required tables if they don't exist"""
    with get_cursor() as cursor:
        # Create passwords table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passwords (
                password TEXT PRIMARY KEY,
                user_id INTEGER
            )
        """)
        
        # Create users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                email TEXT,
                currentClass TEXT
            )
        """)
        
        # Create matches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id TEXT PRIMARY KEY,
                day1 TEXT,
                day2 TEXT,
                day3 TEXT
            )
        """)
        
        logger.info("Database tables created successfully")


def init_database():
    """Initialize the database and create all tables"""
    try:
        create_tables()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
