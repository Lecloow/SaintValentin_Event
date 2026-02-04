"""
Database connection and management module for PostgreSQL.
Handles connection pooling, table creation, and transaction management.
"""
import os
import psycopg2
from psycopg2 import pool
from contextlib import contextmanager
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Connection pool for better performance
connection_pool = None

def init_connection_pool():
    """Initialize the PostgreSQL connection pool."""
    global connection_pool
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL environment variable is not set")
    
    try:
        connection_pool = pool.SimpleConnectionPool(
            1,  # minimum connections
            10,  # maximum connections
            database_url
        )
        logger.info("✅ Connection pool created successfully")
    except Exception as e:
        logger.error(f"❌ Error creating connection pool: {e}")
        raise

def get_connection():
    """Get a connection from the pool."""
    global connection_pool
    
    if connection_pool is None:
        init_connection_pool()
    
    try:
        conn = connection_pool.getconn()
        return conn
    except Exception as e:
        logger.error(f"❌ Error getting connection: {e}")
        raise

def return_connection(conn):
    """Return a connection to the pool."""
    global connection_pool
    
    if connection_pool and conn:
        connection_pool.putconn(conn)

@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    Automatically handles connection acquisition and release.
    """
    conn = get_connection()
    try:
        yield conn
    finally:
        return_connection(conn)

@contextmanager
def get_db_cursor(commit=True):
    """
    Context manager for database cursors.
    Automatically handles transactions.
    
    Args:
        commit: If True, commits the transaction on success. If False, does not commit.
                On exception, always rolls back.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        if commit:
            conn.commit()
    except Exception as e:
        conn.rollback()
        logger.error(f"❌ Database error: {e}")
        raise
    finally:
        cursor.close()
        return_connection(conn)

def init_db():
    """
    Initialize the database by creating all required tables.
    This function is idempotent - it can be called multiple times safely.
    """
    logger.info("🔧 Initializing database tables...")
    
    with get_db_cursor(commit=True) as cursor:
        # Create passwords table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS passwords (
                password TEXT PRIMARY KEY,
                user_id INTEGER
            )
        """)
        logger.info("✅ Table 'passwords' ready")
        
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
        logger.info("✅ Table 'users' ready")
        
        # Create matches table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS matches (
                id TEXT PRIMARY KEY,
                day1 TEXT,
                day2 TEXT,
                day3 TEXT
            )
        """)
        logger.info("✅ Table 'matches' ready")
    
    logger.info("✅ Database initialization complete")

def close_connection_pool():
    """Close all connections in the pool."""
    global connection_pool
    
    if connection_pool:
        connection_pool.closeall()
        logger.info("✅ Connection pool closed")
