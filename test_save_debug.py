#!/usr/bin/env python3
"""
Test the save operation with detailed debugging
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workflows.lead_workflow import get_lead_conversion_workflow

def test_save_with_debug():
    """Test save operation to see the debug output"""
    session_id = "telegram_776451684"

    print(f"=== Testing Save Operation with Debug ===")

    # Create workflow
    workflow = get_lead_conversion_workflow(session_id=session_id)

    # Simulate sending a message to trigger save
    print("\nSending test message...")
    responses = []
    for response in workflow.run("test message"):
        if response.content:
            responses.append(response.content)

    print(f"Response: {responses[0][:50]}...")

if __name__ == "__main__":
    test_save_with_debug()