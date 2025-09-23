#!/usr/bin/env python3
"""
CLI Test Script for Lead Conversion Workflow

This script allows you to test the lead conversion state machine
directly from the command line to validate all stage transitions.
"""

import os
import sys
from datetime import datetime
from colorama import init, Fore, Style

# Add app to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.workflows.lead_workflow import get_lead_conversion_workflow
from app.models.lead_models import ConversationStage

# Initialize colorama for colored output
init(autoreset=True)

def print_header():
    """Print test script header."""
    print("=" * 80)
    print(f"{Fore.CYAN}🚀 Lead Conversion Workflow - Test CLI")
    print(f"{Fore.CYAN}Agilize Contabilidade - Brazilian Accounting Services")
    print("=" * 80)
    print(f"{Fore.YELLOW}💡 Qualification Threshold: R$ 5.000/month")
    print(f"{Fore.YELLOW}📊 Stages: greeting → qualification → data_collection → conversion")
    print(f"{Fore.YELLOW}🔄 Type 'exit' to quit, 'reset' to restart, 'status' for session info")
    print("=" * 80)

def print_stage_info(stage: ConversationStage, qualified: bool = None):
    """Print current stage with color coding."""
    stage_colors = {
        ConversationStage.GREETING: Fore.BLUE,
        ConversationStage.QUALIFICATION: Fore.YELLOW,
        ConversationStage.DATA_COLLECTION: Fore.GREEN,
        ConversationStage.OBJECTION_HANDLING: Fore.MAGENTA,
        ConversationStage.CONVERSION: Fore.CYAN,
        ConversationStage.NURTURING: Fore.RED,
        ConversationStage.COMPLETED: Fore.GREEN
    }

    color = stage_colors.get(stage, Fore.WHITE)
    qualification_status = ""

    if qualified is not None:
        qual_color = Fore.GREEN if qualified else Fore.RED
        qualification_status = f" | {qual_color}{'✅ QUALIFIED' if qualified else '❌ NOT QUALIFIED'}"

    print(f"\n{color}📍 Stage: {stage.value.upper()}{qualification_status}{Style.RESET_ALL}")

def print_session_status(workflow):
    """Print detailed session status."""
    context = workflow._get_context()

    print(f"\n{Fore.CYAN}📊 SESSION STATUS")
    print("-" * 40)
    print(f"Stage: {context.stage.value}")
    print(f"Turns: {context.conversation_turns}")
    print(f"Qualified: {context.is_qualified}")
    if context.qualification_reason:
        print(f"Reason: {context.qualification_reason}")

    # Lead data
    if any([context.lead_data.nome_completo, context.lead_data.email,
            context.lead_data.telefone, context.lead_data.renda_mensal]):
        print(f"\n{Fore.GREEN}👤 LEAD DATA:")
        if context.lead_data.nome_completo:
            print(f"Nome: {context.lead_data.nome_completo}")
        if context.lead_data.email:
            print(f"Email: {context.lead_data.email}")
        if context.lead_data.telefone:
            print(f"Telefone: {context.lead_data.telefone}")
        if context.lead_data.renda_mensal:
            print(f"Renda: R$ {context.lead_data.renda_mensal:,.2f}")

    print(f"\n{Fore.YELLOW}📋 Fields collected: {', '.join(context.fields_collected) or 'None'}")
    print("-" * 40)

def run_cli_test():
    """Run the interactive CLI test."""
    print_header()

    # Create workflow instance
    session_id = f"cli_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    workflow = get_lead_conversion_workflow(session_id=session_id)

    print(f"\n{Fore.GREEN}✅ Session created: {session_id}")
    print(f"{Fore.CYAN}💬 Start typing to test the workflow...")

    # Initial stage
    context = workflow._get_context()
    print_stage_info(context.stage)

    while True:
        try:
            # Get user input
            user_input = input(f"\n{Fore.WHITE}You: ").strip()

            if not user_input:
                continue

            # Handle special commands
            if user_input.lower() == 'exit':
                print(f"\n{Fore.YELLOW}👋 Goodbye! Test session ended.")
                break
            elif user_input.lower() == 'reset':
                workflow.session_state.clear()
                workflow._initialize_context()
                print(f"\n{Fore.GREEN}🔄 Session reset!")
                context = workflow._get_context()
                print_stage_info(context.stage)
                continue
            elif user_input.lower() == 'status':
                print_session_status(workflow)
                continue

            # Process through workflow
            responses = []
            for workflow_response in workflow.run(user_input):
                if workflow_response.content:
                    responses.append(workflow_response.content)

            # Display bot responses
            if responses:
                for i, response in enumerate(responses):
                    if i == 0:
                        print(f"\n{Fore.GREEN}🤖 Bot: {response}")
                    else:
                        print(f"     {response}")
            else:
                print(f"\n{Fore.RED}❌ No response generated")

            # Show updated stage
            context = workflow._get_context()
            print_stage_info(context.stage, context.is_qualified if context.lead_data.renda_mensal else None)

            # Show qualification status change
            if context.qualification_reason:
                qual_color = Fore.GREEN if context.is_qualified else Fore.RED
                print(f"{qual_color}💡 {context.qualification_reason}")

        except KeyboardInterrupt:
            print(f"\n\n{Fore.YELLOW}👋 Test interrupted. Goodbye!")
            break
        except Exception as e:
            print(f"\n{Fore.RED}❌ Error: {str(e)}")

def run_automated_test():
    """Run an automated test sequence."""
    print_header()
    print(f"{Fore.CYAN}🤖 Running automated test sequence...\n")

    session_id = f"auto_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    workflow = get_lead_conversion_workflow(session_id=session_id)

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
        print(f"{Fore.YELLOW}Step {i}: {Fore.WHITE}{message}")

        # Process message
        responses = []
        for workflow_response in workflow.run(message):
            if workflow_response.content:
                responses.append(workflow_response.content)

        # Show response
        if responses:
            print(f"{Fore.GREEN}Bot: {responses[0][:100]}...")

        # Show stage
        context = workflow._get_context()
        print(f"{Fore.BLUE}Stage: {context.stage.value}")

        if context.qualification_reason:
            qual_color = Fore.GREEN if context.is_qualified else Fore.RED
            print(f"{qual_color}{context.qualification_reason}")

        print("-" * 60)

    # Final status
    print(f"\n{Fore.CYAN}🎯 Final Test Results:")
    print_session_status(workflow)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "auto":
        run_automated_test()
    else:
        run_cli_test()