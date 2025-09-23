#!/usr/bin/env python3
"""
Test the fix for loading existing Telegram session
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workflows.lead_workflow import get_lead_conversion_workflow

def test_load_real_session():
    """Test loading the real Telegram session that exists in the database"""
    session_id = "telegram_776451684"

    print(f"=== Testing Load of Real Telegram Session ===")
    print(f"Session ID: {session_id}")

    # Create workflow instance (this should load existing session)
    workflow1 = get_lead_conversion_workflow(session_id=session_id)
    context1 = workflow1._get_context()

    print(f"\nFirst instance:")
    print(f"Stage: {context1.stage.value}")
    print(f"Turns: {context1.conversation_turns}")
    print(f"Messages: {len(context1.messages_exchanged)}")

    if context1.conversation_turns > 0:
        print("✅ SUCCESS: Loaded existing session!")
        print(f"Last message: {context1.messages_exchanged[-1]['content'][:50]}...")
    else:
        print("❌ FAILURE: Session not loaded, created new one")

    # Now send a new message
    print(f"\nSending new message...")
    responses = []
    for response in workflow1.run("Nova mensagem de teste"):
        if response.content:
            responses.append(response.content)

    print(f"Response: {responses[0][:80]}...")

    context2 = workflow1._get_context()
    print(f"\nAfter new message:")
    print(f"Stage: {context2.stage.value}")
    print(f"Turns: {context2.conversation_turns}")

    # Test with another instance
    print(f"\nTesting with new instance...")
    workflow2 = get_lead_conversion_workflow(session_id=session_id)
    context3 = workflow2._get_context()

    print(f"Second instance:")
    print(f"Stage: {context3.stage.value}")
    print(f"Turns: {context3.conversation_turns}")

    if context3.conversation_turns == context2.conversation_turns:
        print("✅ SUCCESS: Session state persisted across instances!")
    else:
        print("❌ FAILURE: Session state not preserved")

if __name__ == "__main__":
    test_load_real_session()