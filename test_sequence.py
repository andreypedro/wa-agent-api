#!/usr/bin/env python3
"""
Test complete workflow sequence
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workflows.lead_workflow import get_lead_conversion_workflow

def test_complete_workflow():
    """Test all workflow stages"""
    workflow = get_lead_conversion_workflow(session_id="test_sequence")

    # Test sequence
    test_messages = [
        "Olá!",
        "Preciso de um contador",
        "Minha renda é de R$ 8.000 por mês",
        "João Silva",
        "joao.silva@email.com",
        "(11) 99999-9999",
        "Sim, quero prosseguir"
    ]

    for i, message in enumerate(test_messages, 1):
        print(f"\n=== Step {i}: '{message}' ===")

        responses = []
        for workflow_response in workflow.run(message):
            if workflow_response.content:
                responses.append(workflow_response.content)

        if responses:
            print(f"Bot: {responses[0][:150]}...")

        # Show stage
        context = workflow._get_context()
        print(f"Stage: {context.stage.value}")

        if context.qualification_reason:
            print(f"Qualification: {context.qualification_reason}")

        if context.lead_data.renda_mensal:
            print(f"Income: R$ {context.lead_data.renda_mensal:,.2f}")

    print(f"\n=== Final State ===")
    context = workflow._get_context()
    print(f"Final Stage: {context.stage.value}")
    print(f"Qualified: {context.is_qualified}")
    print(f"Name: {context.lead_data.nome_completo}")
    print(f"Email: {context.lead_data.email}")
    print(f"Phone: {context.lead_data.telefone}")
    print(f"Fields collected: {context.fields_collected}")

if __name__ == "__main__":
    test_complete_workflow()