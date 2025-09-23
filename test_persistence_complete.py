#!/usr/bin/env python3
"""
Complete test of workflow persistence and data retention
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workflows.lead_workflow import get_lead_conversion_workflow

def test_persistence():
    """Test complete conversation with data persistence"""
    session_id = "test_persistence_user"

    print("=== Testing Complete Persistence ===")

    # Message sequence to test data retention
    messages = [
        "Olá",
        "Rafael Silva",  # Nome
        "rafael@gmail.com",  # Email
        "11987654321",   # Telefone
        "6000"          # Renda
    ]

    for i, message in enumerate(messages, 1):
        print(f"\n--- Message {i}: '{message}' ---")

        try:
            # Create new workflow instance (simulates new request)
            workflow = get_lead_conversion_workflow(session_id=session_id)

            # Send message
            responses = []
            for response in workflow.run(user_input=message):
                if response.content:
                    responses.append(response.content)

            if responses:
                print(f"Bot: {responses[0][:100]}...")

                # Check current data state
                context = workflow._get_context()
                data = context.lead_data
                print(f"Data persisted: nome={data.nome_completo}, email={data.email}, tel={data.telefone}, renda={data.renda_mensal}")

            else:
                print("❌ No response received")

        except Exception as e:
            print(f"❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            break

    print("\n=== Persistence Test Complete ===")

if __name__ == "__main__":
    test_persistence()