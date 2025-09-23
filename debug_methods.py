#!/usr/bin/env python3
"""
Debug Agno storage methods
"""
import sys
import os
import inspect
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_database_storage

print("=== Debugging Agno Storage Methods ===")
storage = get_database_storage()

# Check upsert_session signature
print(f"upsert_session signature: {inspect.signature(storage.upsert_session)}")

# Check get_session signature
print(f"get_session signature: {inspect.signature(storage.get_session)}")

# Try to see the source or docstring
try:
    print(f"upsert_session docstring: {storage.upsert_session.__doc__}")
except:
    pass

try:
    print(f"get_session docstring: {storage.get_session.__doc__}")
except:
    pass

# Test correct API usage
try:
    print("\n=== Testing Correct API Usage ===")

    # Try different parameter combinations for upsert_session
    test_session_id = "test_debug_session"
    test_metadata = {"session_state": {"test": "data"}}

    # Method 1: Basic parameters
    try:
        result = storage.upsert_session(
            user_id="test_user",
            metadata=test_metadata
        )
        print(f"✅ upsert_session with user_id worked: {result}")
    except Exception as e:
        print(f"❌ upsert_session with user_id failed: {e}")

    # Method 2: With session_id as first parameter
    try:
        result = storage.upsert_session(
            test_session_id,
            user_id="test_user",
            metadata=test_metadata
        )
        print(f"✅ upsert_session with positional session_id worked: {result}")
    except Exception as e:
        print(f"❌ upsert_session with positional session_id failed: {e}")

    # Test retrieval
    try:
        result = storage.get_session(test_session_id)
        print(f"✅ get_session worked: {result}")
        if result:
            print(f"Session metadata: {result.metadata}")
    except Exception as e:
        print(f"❌ get_session failed: {e}")

except Exception as e:
    print(f"❌ Error in testing: {e}")