#!/usr/bin/env python3
"""
Debug session loading to see what's happening
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workflows.lead_workflow import get_lead_conversion_workflow

def test_debug_session():
    """Test session loading with debug output"""
    session_id = "debug_session_test"

    print("=== Debug Session Loading ===")

    # First run - create some data
    print("\n--- First Run: Creating data ---")
    workflow1 = get_lead_conversion_workflow(session_id=session_id)

    for response in workflow1.run(user_input="Meu nome é João Silva"):
        if response.content:
            print(f"Response: {response.content[:50]}...")
            break

    # Second run - should load the data
    print("\n--- Second Run: Should load existing data ---")
    workflow2 = get_lead_conversion_workflow(session_id=session_id)

    for response in workflow2.run(user_input="joao@exemplo.com"):
        if response.content:
            print(f"Response: {response.content[:50]}...")
            break

if __name__ == "__main__":
    test_debug_session()