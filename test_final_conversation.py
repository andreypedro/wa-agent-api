#!/usr/bin/env python3
"""
Final comprehensive conversation persistence test
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workflows.lead_workflow import get_lead_conversion_workflow

def test_complete_conversation_persistence():
    """Test complete conversation with separate workflow instances"""
    session_id = "test_final_persistence"

    print("=== FINAL CONVERSATION PERSISTENCE TEST ===")
    print(f"Session ID: {session_id}")

    # Step 1: Initial greeting (Instance 1)
    print("\n1. [Instance 1] User greets")
    workflow1 = get_lead_conversion_workflow(session_id=session_id)
    responses = []
    for response in workflow1.run("Olá!"):
        if response.content:
            responses.append(response.content)
    print(f"Bot: {responses[0][:80]}...")
    context1 = workflow1._get_context()
    print(f"Stage: {context1.stage.value}, Turns: {context1.conversation_turns}")

    # Step 2: Express interest (Instance 2)
    print("\n2. [Instance 2] User expresses accounting interest")
    workflow2 = get_lead_conversion_workflow(session_id=session_id)
    responses = []
    for response in workflow2.run("Preciso de um contador para minha empresa"):
        if response.content:
            responses.append(response.content)
    print(f"Bot: {responses[0][:80]}...")
    context2 = workflow2._get_context()
    print(f"Stage: {context2.stage.value}, Turns: {context2.conversation_turns}")

    # Step 3: Provide income (Instance 3)
    print("\n3. [Instance 3] User provides income")
    workflow3 = get_lead_conversion_workflow(session_id=session_id)
    responses = []
    for response in workflow3.run("Minha renda mensal é de R$ 12.000"):
        if response.content:
            responses.append(response.content)
    print(f"Bot: {responses[0][:80]}...")
    context3 = workflow3._get_context()
    print(f"Stage: {context3.stage.value}, Turns: {context3.conversation_turns}")
    if context3.lead_data.renda_mensal:
        print(f"Income: R$ {context3.lead_data.renda_mensal:,.2f}")

    # Step 4: Provide name (Instance 4)
    print("\n4. [Instance 4] User provides name")
    workflow4 = get_lead_conversion_workflow(session_id=session_id)
    responses = []
    for response in workflow4.run("João Silva"):
        if response.content:
            responses.append(response.content)
    print(f"Bot: {responses[0][:80]}...")
    context4 = workflow4._get_context()
    print(f"Stage: {context4.stage.value}, Turns: {context4.conversation_turns}")
    print(f"Name: {context4.lead_data.nome_completo}")

    # Step 5: Provide email (Instance 5)
    print("\n5. [Instance 5] User provides email")
    workflow5 = get_lead_conversion_workflow(session_id=session_id)
    responses = []
    for response in workflow5.run("joao.silva@email.com"):
        if response.content:
            responses.append(response.content)
    print(f"Bot: {responses[0][:80]}...")
    context5 = workflow5._get_context()
    print(f"Stage: {context5.stage.value}, Turns: {context5.conversation_turns}")
    print(f"Email: {context5.lead_data.email}")

    # Step 6: Provide phone (Instance 6)
    print("\n6. [Instance 6] User provides phone")
    workflow6 = get_lead_conversion_workflow(session_id=session_id)
    responses = []
    for response in workflow6.run("(11) 99999-9999"):
        if response.content:
            responses.append(response.content)
    print(f"Bot: {responses[0][:80]}...")
    context6 = workflow6._get_context()
    print(f"Stage: {context6.stage.value}, Turns: {context6.conversation_turns}")
    print(f"Phone: {context6.lead_data.telefone}")

    # Step 7: Final confirmation (Instance 7)
    print("\n7. [Instance 7] User confirms interest")
    workflow7 = get_lead_conversion_workflow(session_id=session_id)
    responses = []
    for response in workflow7.run("Sim, quero prosseguir com os serviços"):
        if response.content:
            responses.append(response.content)
    print(f"Bot: {responses[0][:80]}...")
    context7 = workflow7._get_context()
    print(f"Stage: {context7.stage.value}, Turns: {context7.conversation_turns}")

    # Final results
    print(f"\n=== FINAL RESULTS ===")
    print(f"✅ Total conversation turns: {context7.conversation_turns}")
    print(f"✅ Final stage: {context7.stage.value}")
    print(f"✅ Qualified: {context7.is_qualified}")
    print(f"✅ Complete lead data collected:")
    print(f"   - Name: {context7.lead_data.nome_completo}")
    print(f"   - Email: {context7.lead_data.email}")
    print(f"   - Phone: {context7.lead_data.telefone}")
    print(f"   - Income: R$ {context7.lead_data.renda_mensal:,.2f}")
    print(f"✅ Fields collected: {context7.fields_collected}")

    # Verify persistence worked
    if (context7.conversation_turns == 7 and
        context7.stage.value == "completed" and
        context7.lead_data.nome_completo and
        context7.lead_data.email and
        context7.lead_data.telefone and
        context7.lead_data.renda_mensal):
        print(f"\n🎉 SUCCESS: Complete conversation persistence working!")
        print(f"   All 7 workflow instances maintained shared state!")
    else:
        print(f"\n❌ FAILURE: Some persistence issues detected")

if __name__ == "__main__":
    test_complete_conversation_persistence()