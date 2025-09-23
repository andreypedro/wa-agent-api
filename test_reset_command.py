#!/usr/bin/env python3
"""
Test the reset functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workflows.lead_workflow import get_lead_conversion_workflow
from app.models.lead_models import ConversationContext

def test_reset_functionality():
    """Test that reset properly clears session state and persistent storage"""
    session_id = "test_reset_session"

    print(f"=== Testing Reset Functionality for {session_id} ===")

    # Step 1: Create initial workflow and add some data
    print("\n1. Creating initial conversation...")
    workflow1 = get_lead_conversion_workflow(session_id=session_id)

    # Simulate a conversation
    responses = []
    for response in workflow1.run("Olá"):
        if response.content:
            responses.append(response.content)
    print(f"Bot response: {responses[0][:50]}...")

    # Add some user data
    for response in workflow1.run("Rafael Silva"):
        if response.content:
            responses.append(response.content)

    context1 = workflow1._get_context()
    print(f"After initial conversation: Turns={context1.conversation_turns}, Messages={len(context1.messages_exchanged)}")

    # Step 2: Simulate the reset operation
    print("\n2. Performing reset operation...")

    # Clear session state in memory
    workflow1.session_state.clear()

    # Initialize a fresh context
    workflow1.session_state["context"] = ConversationContext().model_dump()

    # Clear persistent storage by saving empty state
    workflow1._save_session_state()

    print("Reset completed!")

    # Step 3: Create new workflow instance to verify reset
    print("\n3. Creating new workflow instance to verify reset...")
    workflow2 = get_lead_conversion_workflow(session_id=session_id)
    context2 = workflow2._get_context()

    print(f"After reset: Turns={context2.conversation_turns}, Messages={len(context2.messages_exchanged)}")
    print(f"Stage: {context2.stage.value}")
    print(f"Lead data: {context2.lead_data}")

    # Step 4: Verify reset worked
    if (context2.conversation_turns == 0 and
        len(context2.messages_exchanged) == 0 and
        context2.stage.value == "greeting" and
        not context2.lead_data.nome_completo):
        print("\n✅ SUCCESS: Reset functionality working correctly!")
        print("   - Conversation turns reset to 0")
        print("   - Messages cleared")
        print("   - Stage reset to greeting")
        print("   - Lead data cleared")
    else:
        print("\n❌ FAILURE: Reset did not work properly")
        print(f"   - Turns: {context2.conversation_turns} (should be 0)")
        print(f"   - Messages: {len(context2.messages_exchanged)} (should be 0)")
        print(f"   - Stage: {context2.stage.value} (should be greeting)")

if __name__ == "__main__":
    test_reset_functionality()