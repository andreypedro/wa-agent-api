"""
Database configuration for Agno chat history storage.
Supports SQLite and PostgreSQL databases.
"""

import os
from typing import Optional
from dotenv import load_dotenv
from agno.db.sqlite import SqliteDb
from agno.db.postgres import PostgresDb

load_dotenv()

def get_database_storage():
    """
    Get the appropriate database storage based on DATABASE_URL environment variable.
    
    Returns:
        Database storage instance for Agno agents
        
    Examples:
        - SQLite: sqlite:///./chat_history.db
        - PostgreSQL: postgresql://user:password@localhost:5432/chat_history
    """
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        print("[DATABASE] No DATABASE_URL configured, using in-memory storage (history will be lost on restart)")
        return None
    
    try:
        if database_url.startswith('sqlite'):
            # Extract the database file path from the URL
            db_path = database_url.replace('sqlite:///', '')
            print(f"[DATABASE] Using SQLite database: {db_path}")
            return SqliteDb(db_file=db_path)

        elif database_url.startswith('postgresql'):
            print(f"[DATABASE] Using PostgreSQL database")
            return PostgresDb(db_url=database_url)

        else:
            print(f"[DATABASE] Unsupported database URL format: {database_url}")
            print("[DATABASE] Supported formats: sqlite:///path/to/db.db or postgresql://user:pass@host:port/db")
            return None
            
    except Exception as e:
        print(f"[DATABASE] Error initializing database storage: {str(e)}")
        print("[DATABASE] Falling back to in-memory storage")
        return None

def get_session_storage():
    """
    Get session storage for maintaining conversation context.
    This is the same as get_database_storage() but with a clearer name for session management.
    """
    return get_database_storage()
