#!/usr/bin/env python3
"""
Debug the exact session loading issue in production
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workflows.lead_workflow import get_lead_conversion_workflow

def debug_session_loading():
    """Debug session loading for real Telegram session"""
    session_id = "telegram_776451684"  # Real user session ID

    print(f"=== Debugging Session Loading for {session_id} ===")

    # Create workflow and check what happens during initialization
    print("\n1. Creating workflow...")
    workflow = get_lead_conversion_workflow(session_id=session_id)

    print(f"Storage: {workflow.storage}")
    print(f"Session ID: {workflow.session_id}")
    print(f"Session state after init: {workflow.session_state}")

    # Try to manually load session
    print("\n2. Attempting manual session load...")
    loaded = workflow._load_session_state()
    print(f"Load result: {loaded}")
    print(f"Session state after load: {workflow.session_state}")

    # Try to get session directly from storage
    print("\n3. Direct storage query...")
    try:
        from agno.db.base import SessionType
        session_data = workflow.storage.get_session(
            session_id=session_id,
            session_type=SessionType.WORKFLOW
        )
        print(f"Direct get_session result: {session_data}")
        if session_data:
            print(f"Session metadata: {session_data.metadata}")
    except Exception as e:
        print(f"Direct get_session error: {e}")

    # Check if there are any sessions in storage
    print("\n4. List all sessions...")
    try:
        sessions = workflow.storage.get_sessions(user_id=None)
        print(f"All sessions: {sessions}")
    except Exception as e:
        print(f"Error listing sessions: {e}")

    # Try a test session
    print("\n5. Test session save/load...")
    test_session_id = "test_debug_session_new"
    test_workflow = get_lead_conversion_workflow(session_id=test_session_id)

    # Save something
    test_workflow.session_state["test"] = "value"
    test_workflow._save_session_state()

    # Try to load it with new instance
    test_workflow2 = get_lead_conversion_workflow(session_id=test_session_id)
    loaded2 = test_workflow2._load_session_state()
    print(f"Test save/load result: {loaded2}")
    print(f"Test session state: {test_workflow2.session_state}")

if __name__ == "__main__":
    debug_session_loading()