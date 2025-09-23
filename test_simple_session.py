#!/usr/bin/env python3
"""
Simple test to check if session_state saves automatically
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workflows.lead_workflow import get_lead_conversion_workflow

def test_simple_session():
    """Test if session_state changes are automatically saved"""
    session_id = "simple_session_test"

    print("=== Simple Session Test ===")

    # Run 1: Add data to session_state
    print("\n--- Run 1: Adding data to session_state ---")
    workflow1 = get_lead_conversion_workflow(session_id=session_id)

    print(f"Before: session_state = {workflow1.session_state}")
    workflow1.session_state["test_data"] = {"message": "Hello World", "number": 42}
    print(f"After: session_state = {workflow1.session_state}")

    # Manually call run to trigger any potential save
    list(workflow1.run(user_input="test"))

    # Run 2: Check if data persists
    print("\n--- Run 2: Checking if data persists ---")
    workflow2 = get_lead_conversion_workflow(session_id=session_id)
    print(f"New instance session_state = {workflow2.session_state}")

    if "test_data" in workflow2.session_state:
        print("✅ SUCCESS: session_state persisted!")
    else:
        print("❌ FAILURE: session_state did not persist")

if __name__ == "__main__":
    test_simple_session()