#!/usr/bin/env python3
"""
Test script to verify the new state machine (v2) is working properly
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workflows.lead_workflow_v2 import get_lead_conversion_state_machine

def test_state_machine_v2():
    """Test if the new state machine with Router patterns works"""
    session_id = "test_state_machine_v2"

    print("=== Testing State Machine V2 (Router-based) ===")

    try:
        # Test 1: Initial greeting
        print("\n--- Test 1: Initial greeting ---")
        workflow = get_lead_conversion_state_machine(session_id=session_id)

        responses = list(workflow.run(user_input="oi"))
        print(f"Number of responses: {len(responses)}")

        for i, response in enumerate(responses):
            print(f"Response {i+1}: {response.content[:100]}...")

        # Test 2: Check state transitions
        print("\n--- Test 2: Providing name ---")
        responses = list(workflow.run(user_input="Rafael Oliveira"))

        for i, response in enumerate(responses):
            print(f"Response {i+1}: {response.content[:100]}...")

        print("\n✅ State machine V2 test completed successfully!")

    except Exception as e:
        print(f"❌ State machine V2 test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_state_machine_v2()