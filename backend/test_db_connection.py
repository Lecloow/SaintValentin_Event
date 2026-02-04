#!/usr/bin/env python3
"""
Simple validation script to test PostgreSQL connection and database setup.
This script verifies that the database connection works and tables are created.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def main():
    print("🔍 PostgreSQL Connection Test")
    print("=" * 50)
    
    # Check if DATABASE_URL is set
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ ERROR: DATABASE_URL environment variable is not set!")
        print("   Please create a .env file with DATABASE_URL")
        print("   Example: DATABASE_URL=postgresql://user:pass@localhost:5432/dbname")
        return False
    
    print(f"✅ DATABASE_URL is set")
    # Hide password in output
    safe_url = database_url.split('@')[1] if '@' in database_url else 'configured'
    print(f"   Connection: ...@{safe_url}")
    
    # Test import of database module
    try:
        from database import init_db, get_db_cursor
        print("✅ database.py module imported successfully")
    except ImportError as e:
        print(f"❌ ERROR: Failed to import database module: {e}")
        return False
    
    # Test database connection
    try:
        print("\n🔧 Testing database connection...")
        init_db()
        print("✅ Database connection successful!")
        print("✅ Tables created/verified successfully!")
    except Exception as e:
        print(f"❌ ERROR: Database connection failed: {e}")
        print("\nPossible issues:")
        print("  1. PostgreSQL server is not running")
        print("  2. Database does not exist")
        print("  3. Invalid credentials in DATABASE_URL")
        print("  4. Network connectivity issues")
        return False
    
    # Test table existence
    try:
        print("\n🔍 Verifying tables...")
        with get_db_cursor(commit=False) as cursor:
            # Check passwords table
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'passwords'
            """)
            if cursor.fetchone()[0] == 1:
                print("✅ Table 'passwords' exists")
            else:
                print("❌ Table 'passwords' not found")
            
            # Check users table
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'users'
            """)
            if cursor.fetchone()[0] == 1:
                print("✅ Table 'users' exists")
            else:
                print("❌ Table 'users' not found")
            
            # Check matches table
            cursor.execute("""
                SELECT COUNT(*) FROM information_schema.tables 
                WHERE table_name = 'matches'
            """)
            if cursor.fetchone()[0] == 1:
                print("✅ Table 'matches' exists")
            else:
                print("❌ Table 'matches' not found")
            
            # Get row counts
            cursor.execute("SELECT COUNT(*) FROM users")
            user_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM passwords")
            password_count = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM matches")
            match_count = cursor.fetchone()[0]
            
            print(f"\n📊 Database Statistics:")
            print(f"   Users: {user_count}")
            print(f"   Passwords: {password_count}")
            print(f"   Matches: {match_count}")
            
    except Exception as e:
        print(f"❌ ERROR: Failed to verify tables: {e}")
        return False
    
    print("\n" + "=" * 50)
    print("✅ All checks passed! Database is ready.")
    print("\nYou can now run the application:")
    print("   uvicorn main:app --reload")
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
