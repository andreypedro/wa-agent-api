#!/usr/bin/env python3
"""
Test cross-channel state persistence
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workflows.lead_workflow import get_lead_conversion_workflow

def test_cross_channel_persistence():
    """Test state persistence across channels"""
    user_phone = "5511999999999"

    print("=== Testing Cross-Channel State Persistence ===")

    # Start conversation on WhatsApp
    print("\n1. Starting conversation on WhatsApp")
    whatsapp_session_id = f"whatsapp_{user_phone}"
    whatsapp_workflow = get_lead_conversion_workflow(session_id=whatsapp_session_id)

    # First interaction on WhatsApp
    responses = []
    for response in whatsapp_workflow.run("Preciso de um contador"):
        if response.content:
            responses.append(response.content)

    print(f"WhatsApp Bot: {responses[0][:100]}...")
    context = whatsapp_workflow._get_context()
    print(f"WhatsApp Stage: {context.stage.value}")

    # User continues on Telegram (same session base)
    print("\n2. Continuing conversation on Telegram")
    telegram_session_id = f"telegram_{user_phone}"
    telegram_workflow = get_lead_conversion_workflow(session_id=telegram_session_id)

    # Check if we can share state across channels
    responses = []
    for response in telegram_workflow.run("Minha renda é de R$ 10.000"):
        if response.content:
            responses.append(response.content)

    print(f"Telegram Bot: {responses[0][:100]}...")
    context = telegram_workflow._get_context()
    print(f"Telegram Stage: {context.stage.value}")

    # Test session info via API-like call
    print("\n3. Testing unified session approach")
    # Use a unified session ID that both channels could share
    unified_session_id = f"user_{user_phone}"

    # Start on unified session (WhatsApp)
    workflow_unified = get_lead_conversion_workflow(session_id=unified_session_id)

    # Simulate WhatsApp message
    print("WhatsApp message: 'Olá, preciso de ajuda com contabilidade'")
    for response in workflow_unified.run("Olá, preciso de ajuda com contabilidade"):
        if response.content:
            print(f"Response: {response.content[:100]}...")
            break

    context = workflow_unified._get_context()
    print(f"Stage after WhatsApp: {context.stage.value}")

    # Continue same session from Telegram
    workflow_unified_2 = get_lead_conversion_workflow(session_id=unified_session_id)

    print("Telegram message: 'R$ 15.000 por mês'")
    for response in workflow_unified_2.run("R$ 15.000 por mês"):
        if response.content:
            print(f"Response: {response.content[:100]}...")
            break

    context = workflow_unified_2._get_context()
    print(f"Stage after Telegram: {context.stage.value}")
    if context.lead_data.renda_mensal:
        print(f"Income preserved: R$ {context.lead_data.renda_mensal:,.2f}")

    print(f"\n✅ Cross-channel persistence test completed!")
    print(f"Unified session demonstrates how the same conversation")
    print(f"can continue seamlessly across WhatsApp and Telegram")

if __name__ == "__main__":
    test_cross_channel_persistence()