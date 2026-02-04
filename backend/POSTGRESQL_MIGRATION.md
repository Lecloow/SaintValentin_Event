# PostgreSQL Migration Guide

This guide explains how to run the migrated application with PostgreSQL.

## Prerequisites

1. Python 3.9+
2. PostgreSQL database (local or Render-hosted)

## Setup Instructions

### Local Development

1. **Install PostgreSQL** (if not already installed)
   - macOS: `brew install postgresql`
   - Ubuntu/Debian: `sudo apt-get install postgresql postgresql-contrib`
   - Windows: Download from [postgresql.org](https://www.postgresql.org/download/)

2. **Create a local database**
   ```bash
   # Start PostgreSQL service
   # macOS: brew services start postgresql
   # Linux: sudo systemctl start postgresql
   
   # Create database
   createdb saintvalentin
   
   # Or using psql:
   psql -U postgres
   CREATE DATABASE saintvalentin;
   \q
   ```

3. **Configure environment variables**
   ```bash
   cd backend
   cp .env.example .env
   # Edit .env and set your DATABASE_URL
   # Example: DATABASE_URL=postgresql://postgres:password@localhost:5432/saintvalentin
   ```

4. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

5. **Run the application**
   ```bash
   uvicorn main:app --reload
   ```
   
   The database tables will be created automatically on first run!

### Render Deployment

1. **Create a PostgreSQL database on Render**
   - Go to your Render dashboard
   - Create a new PostgreSQL database
   - Copy the internal DATABASE_URL

2. **Deploy the backend**
   - Create a new Web Service on Render
   - Connect your repository
   - Set the following:
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
     - **Environment Variables**: 
       - `DATABASE_URL`: Your Render PostgreSQL internal URL
       - `EMAIL`: Your email address
       - `PASSWORD`: Your email app password

3. **The database will initialize automatically** when the application starts!

## Migration Changes

### Key Differences from SQLite

1. **Connection Management**: 
   - Uses connection pooling via `database.py`
   - Connections are acquired and released automatically

2. **SQL Syntax Changes**:
   - Parameter placeholders: `?` → `%s`
   - UPSERT syntax: `INSERT OR REPLACE` → `INSERT ... ON CONFLICT ... DO UPDATE`

3. **Database File**:
   - No more `data.db` file
   - Data stored in PostgreSQL server
   - `/download-db/` endpoint now exports to JSON format

### API Endpoints

All endpoints remain the same:
- `POST /login` - User login with password
- `POST /import` - Import users from Excel file
- `POST /upload-xlsx/` - Upload Excel file
- `GET /download-db/` - Export database to JSON (changed from SQLite file)
- `POST /send-emails` - Send password emails
- `POST /createMatches` - Create matches

## Troubleshooting

### Connection Errors

If you get connection errors:
1. Check DATABASE_URL is set correctly
2. Ensure PostgreSQL service is running
3. Verify database exists and credentials are correct

### Table Creation Issues

If tables aren't created:
1. Check logs for error messages
2. Ensure database user has CREATE TABLE permissions
3. Try connecting manually: `psql $DATABASE_URL`

### Migration from Existing SQLite Data

To migrate existing SQLite data to PostgreSQL:

```python
import sqlite3
import psycopg2
import os

# Connect to SQLite
sqlite_conn = sqlite3.connect('data.db')
sqlite_cursor = sqlite_conn.cursor()

# Connect to PostgreSQL
pg_conn = psycopg2.connect(os.getenv('DATABASE_URL'))
pg_cursor = pg_conn.cursor()

# Migrate users
sqlite_cursor.execute("SELECT * FROM users")
for row in sqlite_cursor.fetchall():
    pg_cursor.execute(
        "INSERT INTO users VALUES (%s, %s, %s, %s, %s) ON CONFLICT DO NOTHING",
        row
    )

# Migrate passwords
sqlite_cursor.execute("SELECT * FROM passwords")
for row in sqlite_cursor.fetchall():
    pg_cursor.execute(
        "INSERT INTO passwords VALUES (%s, %s) ON CONFLICT DO NOTHING",
        row
    )

# Migrate matches
sqlite_cursor.execute("SELECT * FROM matches")
for row in sqlite_cursor.fetchall():
    pg_cursor.execute(
        "INSERT INTO matches VALUES (%s, %s, %s, %s) ON CONFLICT DO NOTHING",
        row
    )

pg_conn.commit()
print("Migration complete!")
```

## Testing

Test the application:
```bash
# Start the server
uvicorn main:app --reload

# Open browser to test API docs
open http://localhost:8000/docs
```

Test endpoints:
1. Upload an Excel file via `/upload-xlsx/`
2. Import users via `/import`
3. Test login via `/login`
4. Download data via `/download-db/`
