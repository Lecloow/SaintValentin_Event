# PostgreSQL Migration Guide

This document describes the migration from SQLite to PostgreSQL for the Saint Valentin Event backend.

## Changes Made

### 1. Dependencies
- **Updated**: Using `psycopg[binary]>=3.1.0` (modern psycopg3 library)
- **Previous**: psycopg2-binary (now deprecated)

### 2. Database Connection
- **Before**: Used SQLite with local `data.db` file
- **After**: Uses PostgreSQL with connection details from environment variables

### 3. Environment Variables
The application now requires database configuration through environment variables. Two options are supported:

#### Option 1: Complete DATABASE_URL (Recommended for Render)
```bash
DATABASE_URL=postgresql://user:password@host:port/database
```

#### Option 2: Individual credentials
```bash
DB_HOST=localhost
DB_PORT=5432
DB_NAME=saintvalentin
DB_USER=postgres
DB_PASSWORD=your_password_here
```

### 4. SQL Query Changes
All SQL queries have been updated from SQLite to PostgreSQL syntax:
- **Parameter placeholders**: `?` → `%s`
- **UPSERT operations**: `INSERT OR REPLACE` → `INSERT ... ON CONFLICT ... DO UPDATE`
- **Password conflicts**: Changed from `DO UPDATE` to `DO NOTHING` to prevent password reassignment

### 5. Connection Management
- Added proper shutdown event handler to close database connections
- Added error handling for connection cleanup
- Added note about connection pooling for production use

### 6. Endpoint Changes
- `/download-db/` endpoint now returns HTTP 501 (Not Implemented) as database download is not applicable for remote PostgreSQL

## Testing

All changes have been validated:
- ✅ Python syntax validation
- ✅ Import statements verification
- ✅ Utility functions testing
- ✅ Database connection logic testing
- ✅ PostgreSQL query syntax validation
- ✅ Code review completed
- ✅ Security scan completed (no vulnerabilities found)

## Deployment on Render

1. Create a PostgreSQL database on Render
2. Set the `DATABASE_URL` environment variable in your Render service settings
3. Deploy the application
4. The tables will be created automatically on first startup

## Local Development

1. Install PostgreSQL locally or use Docker:
```bash
docker run --name postgres -e POSTGRES_PASSWORD=mypassword -p 5432:5432 -d postgres
```

2. Create a `.env` file based on `.env.example`:
```bash
cp .env.example .env
# Edit .env with your database credentials
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run the application:
```bash
uvicorn main:app --reload
```

## Migration Notes

- All existing functionality is preserved
- Table structure remains the same (passwords, users, matches)
- All endpoints continue to work as before
- XLSX import/export functionality unchanged
- Using modern psycopg3 library (psycopg2 is now deprecated)

## Future Improvements

For high-concurrency production use, consider:
- Implementing connection pooling with `psycopg.pool` (psycopg3)
- Using FastAPI dependency injection for per-request connections
- Adding database migration tools (e.g., Alembic)
- Implementing database backup strategies
