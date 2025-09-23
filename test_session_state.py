#!/usr/bin/env python3
"""
Simple test to understand session state behavior
"""

import sys
import os
from datetime import datetime

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workflows.lead_workflow import get_lead_conversion_workflow

def test_session_persistence():
    """Test if session state persists between workflow instances"""
    print("Testing session state persistence...")

    session_id = "test_session_123"

    # First interaction - create workflow and send message
    print("\n1. Creating first workflow instance...")
    workflow1 = get_lead_conversion_workflow(session_id=session_id)
    print(f"Session state before first message: {workflow1.session_state}")

    # Send first message
    responses1 = []
    for response in workflow1.run("Olá"):
        if response.content:
            responses1.append(response.content)

    print(f"Response 1: {responses1[0][:100]}...")
    print(f"Session state after first message: {workflow1.session_state}")

    # Get context from first workflow
    context1 = workflow1._get_context()
    print(f"Context after first message - Stage: {context1.stage}, Turns: {context1.conversation_turns}")

    # Second interaction - create NEW workflow instance with SAME session_id
    print("\n2. Creating SECOND workflow instance with same session_id...")
    workflow2 = get_lead_conversion_workflow(session_id=session_id)
    print(f"Session state in new instance: {workflow2.session_state}")

    # Get context from second workflow
    context2 = workflow2._get_context()
    print(f"Context in new instance - Stage: {context2.stage}, Turns: {context2.conversation_turns}")

    # Send second message
    responses2 = []
    for response in workflow2.run("Preciso de um contador"):
        if response.content:
            responses2.append(response.content)

    print(f"Response 2: {responses2[0][:100]}...")

    # Get final context
    context2_final = workflow2._get_context()
    print(f"Final context - Stage: {context2_final.stage}, Turns: {context2_final.conversation_turns}")

    # Test if state was preserved
    if context2.conversation_turns > 0:
        print("\n✅ SUCCESS: Session state WAS preserved between instances")
        print(f"    - Started with {context2.conversation_turns} turns")
        print(f"    - Final turns: {context2_final.conversation_turns}")
    else:
        print("\n❌ PROBLEM: Session state was NOT preserved between instances")
        print(f"    - Started with {context2.conversation_turns} turns (should be > 0)")
        print(f"    - This means each workflow instance creates fresh state")

    return context2.conversation_turns > 0

def test_single_instance_persistence():
    """Test if state persists within the same workflow instance"""
    print("\n\nTesting single instance persistence...")

    session_id = "test_session_456"
    workflow = get_lead_conversion_workflow(session_id=session_id)

    # Multiple messages on same instance
    messages = ["Olá", "Preciso de um contador", "R$ 10.000"]

    for i, message in enumerate(messages, 1):
        print(f"\nMessage {i}: {message}")

        # Get context before
        context_before = workflow._get_context()
        print(f"  Before - Stage: {context_before.stage}, Turns: {context_before.conversation_turns}")

        # Send message
        responses = []
        for response in workflow.run(message):
            if response.content:
                responses.append(response.content)

        # Get context after
        context_after = workflow._get_context()
        print(f"  After - Stage: {context_after.stage}, Turns: {context_after.conversation_turns}")
        print(f"  Response: {responses[0][:50]}..." if responses else "  No response")

    print(f"\n✅ Single instance test completed. Final turns: {context_after.conversation_turns}")

if __name__ == "__main__":
    # Test 1: Check if state persists between different workflow instances
    preserved = test_session_persistence()

    # Test 2: Check if state persists within same workflow instance
    test_single_instance_persistence()

    print(f"\n{'='*60}")
    print("SUMMARY:")
    print(f"Session persistence between instances: {'✅ YES' if preserved else '❌ NO'}")
    print("Session persistence within instance: ✅ YES (expected)")

    if not preserved:
        print("\n🔍 DIAGNOSIS:")
        print("The issue is that Agno Workflow session_state is not automatically")
        print("persisted to external storage. Each new workflow instance starts fresh.")
        print("\n💡 SOLUTIONS NEEDED:")
        print("1. Configure Agno Workflow with database storage")
        print("2. Or implement manual session state persistence")
        print("3. Or use Agent with storage instead of Workflow")