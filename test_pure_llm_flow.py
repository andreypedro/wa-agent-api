#!/usr/bin/env python3
"""
Test the pure LLM-driven conversation flow
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workflows.lead_workflow import get_lead_conversion_workflow

def test_pure_llm_flow():
    """Test the pure LLM-driven conversation flow"""
    session_id = "test_pure_llm_flow"

    print("=== Testing Pure LLM-Driven Flow ===")

    # Create workflow
    workflow = get_lead_conversion_workflow(session_id=session_id)

    # Test conversation flow
    test_messages = [
        "Olá",
        "Rafael Silva",
        "rafael.silva@gmail.com",
        "11988919158",
        "6000",  # This should be understood as R$ 6,000
    ]

    print("\n1. Testing conversation flow:")
    for i, message in enumerate(test_messages, 1):
        print(f"\n--- Turn {i}: User says '{message}' ---")

        try:
            responses = []
            for response in workflow.run(message):
                if response.content:
                    responses.append(response.content)

            if responses:
                print(f"Bot: {responses[0][:100]}...")
            else:
                print("Bot: [No response]")

            # Check current data state
            context = workflow._get_context()
            data = context.lead_data
            print(f"Data: nome={data.nome_completo}, email={data.email}, tel={data.telefone}, renda={data.renda_mensal}")

        except Exception as e:
            print(f"ERROR: {e}")
            break

    print("\n=== Test Complete ===")

if __name__ == "__main__":
    test_pure_llm_flow()