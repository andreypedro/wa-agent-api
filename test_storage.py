#!/usr/bin/env python3
"""
Test storage configuration for workflow
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.workflows.lead_workflow import get_lead_conversion_workflow
    print("✅ Testing workflow with storage configuration...")

    # Test workflow creation
    workflow = get_lead_conversion_workflow(session_id="test_storage")
    print("✅ Successfully created workflow with storage")

    # Test first message
    print("\n=== First Message ===")
    responses = []
    for response in workflow.run("Preciso de um contador"):
        if response.content:
            responses.append(response.content)
            print(f"🤖 Response: {response.content[:100]}...")

    context = workflow._get_context()
    print(f"Stage after first message: {context.stage.value}")

    # Test second message with new workflow instance (this should restore state)
    print("\n=== Second Message (New Instance) ===")
    workflow2 = get_lead_conversion_workflow(session_id="test_storage")  # Same session ID

    responses = []
    for response in workflow2.run("R$ 8000"):
        if response.content:
            responses.append(response.content)
            print(f"🤖 Response: {response.content[:100]}...")

    context2 = workflow2._get_context()
    print(f"Stage after second message: {context2.stage.value}")

    if context2.stage.value != "greeting":
        print("✅ SUCCESS: Conversation state was preserved!")
        if context2.lead_data.renda_mensal:
            print(f"✅ Income preserved: R$ {context2.lead_data.renda_mensal:,.2f}")
    else:
        print("❌ FAILURE: Conversation state was reset")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()