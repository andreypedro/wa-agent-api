#!/usr/bin/env python3
"""
Test session continuity - verify that data persists across multiple workflow instances
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workflows.lead_workflow import get_lead_conversion_workflow

def test_session_continuity():
    """Test that data persists across multiple workflow instances with same session_id"""
    session_id = "test_continuity_session"

    print("=== Testing Session Continuity ===")

    # First workflow run - collect name
    print("\n--- First workflow run: Collecting name ---")
    workflow1 = get_lead_conversion_workflow(session_id=session_id)

    for response in workflow1.run(user_input="Olá, meu nome é João da Silva"):
        if response.content:
            print(f"Bot: {response.content[:80]}...")
            break

    # Check data after first run
    context1 = workflow1._get_context()
    print(f"After run 1 - nome: {context1.lead_data.nome_completo}, turns: {context1.conversation_turns}")

    # Second workflow run - should remember the name and ask for email
    print("\n--- Second workflow run: Should remember name ---")
    workflow2 = get_lead_conversion_workflow(session_id=session_id)  # NEW INSTANCE!

    for response in workflow2.run(user_input="joao@exemplo.com"):
        if response.content:
            print(f"Bot: {response.content[:80]}...")
            break

    # Check data after second run
    context2 = workflow2._get_context()
    print(f"After run 2 - nome: {context2.lead_data.nome_completo}, email: {context2.lead_data.email}, turns: {context2.conversation_turns}")

    # Third workflow run - should remember name AND email
    print("\n--- Third workflow run: Should remember name and email ---")
    workflow3 = get_lead_conversion_workflow(session_id=session_id)  # ANOTHER NEW INSTANCE!

    for response in workflow3.run(user_input="11987654321"):
        if response.content:
            print(f"Bot: {response.content[:80]}...")
            break

    # Check final data
    context3 = workflow3._get_context()
    print(f"After run 3 - nome: {context3.lead_data.nome_completo}, email: {context3.lead_data.email}, tel: {context3.lead_data.telefone}, turns: {context3.conversation_turns}")

    # Verify data persistence (conversation_turns resets per workflow instance, but data should persist)
    success = (
        context3.lead_data.nome_completo == "João da Silva" and
        context3.lead_data.email == "joao@exemplo.com" and
        context3.lead_data.telefone == "11987654321"
    )

    print(f"\n=== Final Results ===")
    print(f"Nome: {context3.lead_data.nome_completo} (Expected: João da Silva)")
    print(f"Email: {context3.lead_data.email} (Expected: joao@exemplo.com)")
    print(f"Telefone: {context3.lead_data.telefone} (Expected: 11987654321)")

    if success:
        print("\n✅ SUCCESS: Session state persisted correctly across multiple workflow instances!")
        print("✅ Name, email, and phone were all retained between separate workflow runs.")
        print("✅ The bot correctly remembered previous data and continued the conversation!")
    else:
        print("\n❌ FAILURE: Session state did not persist properly")
        print(f"   Expected: João da Silva / joao@exemplo.com / 11987654321")
        print(f"   Got: {context3.lead_data.nome_completo} / {context3.lead_data.email} / {context3.lead_data.telefone}")

    print("\n=== Session Continuity Test Complete ===")

if __name__ == "__main__":
    test_session_continuity()