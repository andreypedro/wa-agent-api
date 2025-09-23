#!/usr/bin/env python3
"""
Debug storage object to understand its structure
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_database_storage

print("=== Debugging Storage Object ===")
storage = get_database_storage()

print(f"Storage object: {storage}")
print(f"Storage type: {type(storage)}")
print(f"Storage attributes: {dir(storage)}")

if hasattr(storage, 'connection'):
    print(f"Has connection: {storage.connection}")
    print(f"Connection type: {type(storage.connection)}")

    # Try to list tables
    try:
        cursor = storage.connection.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"Existing tables: {tables}")
    except Exception as e:
        print(f"Error listing tables: {e}")

if hasattr(storage, 'db_file'):
    print(f"DB file: {storage.db_file}")

# Test basic operations
try:
    # Create test table
    cursor = storage.connection.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS test_sessions (
            session_id TEXT PRIMARY KEY,
            data TEXT
        )
    """)

    # Insert test data
    cursor.execute("INSERT OR REPLACE INTO test_sessions (session_id, data) VALUES (?, ?)",
                   ("test_session", "test_data"))
    storage.connection.commit()

    # Read test data
    cursor.execute("SELECT data FROM test_sessions WHERE session_id = ?", ("test_session",))
    result = cursor.fetchone()
    print(f"Test data read: {result}")

    print("✅ Direct SQLite operations work!")

except Exception as e:
    print(f"❌ Error with SQLite operations: {e}")