#!/usr/bin/env python3
"""
Simple test script for the lead conversion workflow
"""

import sys
import os

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from app.workflows.lead_workflow import get_lead_conversion_workflow
    print("✅ Successfully imported workflow")

    # Test workflow creation
    workflow = get_lead_conversion_workflow(session_id="test_simple")
    print("✅ Successfully created workflow")

    # Test simple message
    responses = []
    for response in workflow.run("Ola!"):
        if response.content:
            responses.append(response.content)
            print(f"🤖 Response: {response.content[:100]}...")

    print("✅ Test completed successfully")

except Exception as e:
    print(f"❌ Error: {str(e)}")
    import traceback
    traceback.print_exc()