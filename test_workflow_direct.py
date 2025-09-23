#!/usr/bin/env python3
"""
Direct test of the workflow to verify the fix
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workflows.lead_workflow import get_lead_conversion_workflow

def test_workflow():
    """Test the workflow directly"""
    session_id = "test_workflow_fix"

    print("=== Testing Fixed Workflow ===")

    try:
        # Create workflow
        workflow = get_lead_conversion_workflow(session_id=session_id)
        print(f"✅ Workflow created successfully with session: {session_id}")

        # Test with user input
        responses = []
        for response in workflow.run(user_input="Olá, tudo bem?"):
            if response.content:
                responses.append(response.content)
                print(f"✅ Got response: {response.content[:50]}...")

        if responses:
            print("✅ SUCCESS: Workflow execution completed without errors")
            print(f"   Response: {responses[0]}")
        else:
            print("❌ FAILURE: No responses received")

    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_workflow()