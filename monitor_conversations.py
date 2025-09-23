#!/usr/bin/env python3
"""
Simple real-time conversation data monitor.
Shows what data is being saved during user conversations.
"""

import sqlite3
import json
import time
import os
from datetime import datetime
from typing import Dict, Any

def format_timestamp(timestamp):
    """Convert timestamp to readable format."""
    if timestamp:
        return datetime.fromtimestamp(timestamp).strftime("%H:%M:%S")
    return "N/A"

def format_json(data, max_length=100):
    """Format JSON data for display."""
    if not data:
        return "None"
    
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            return data[:max_length] + "..." if len(data) > max_length else data
    
    formatted = json.dumps(data, ensure_ascii=False, indent=2)
    if len(formatted) > max_length:
        return formatted[:max_length] + "..."
    return formatted

def get_latest_sessions(db_path="chat_history.db", limit=5):
    """Get the latest conversation sessions."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get latest sessions from workflow_sessions_v2
        cursor.execute("""
            SELECT session_id, user_id, session_data, workflow_data, 
                   created_at, updated_at, workflow_name
            FROM workflow_sessions_v2 
            ORDER BY updated_at DESC 
            LIMIT ?
        """, (limit,))
        
        sessions = cursor.fetchall()
        conn.close()
        
        return sessions
    except Exception as e:
        print(f"Error reading database: {e}")
        return []

def extract_conversation_data(session_data):
    """Extract key conversation data from session."""
    if not session_data:
        return {}

    try:
        if isinstance(session_data, str):
            data = json.loads(session_data)
        else:
            data = session_data

        # Extract key fields
        extracted = {}

        # Check if data is nested in 'context'
        if 'context' in data:
            context = data['context']

            # Current stage
            extracted['stage'] = context.get('stage', 'N/A')

            # Lead data
            if 'lead_data' in context:
                lead = context['lead_data']
                extracted['nome_cliente'] = lead.get('nome_cliente', 'N/A')
                extracted['nome_completo'] = lead.get('nome_completo', 'N/A')
                extracted['tipo_interesse'] = lead.get('tipo_interesse', 'N/A')
                extracted['email'] = lead.get('email', 'N/A')
                extracted['telefone'] = lead.get('telefone', 'N/A')
                extracted['cpf'] = lead.get('cpf', 'N/A')

            # Business profile data
            if 'business_profile' in context:
                business = context['business_profile']
                extracted['tipo_negocio'] = business.get('tipo_negocio', 'N/A')
                extracted['estrutura_societaria'] = business.get('estrutura_societaria', 'N/A')
                extracted['faturamento_mei_ok'] = business.get('faturamento_mei_ok', 'N/A')

            # Proposal status
            if 'proposal_status' in context:
                proposal = context['proposal_status']
                extracted['aceite_proposta'] = proposal.get('aceite_proposta', 'N/A')

            # Contract data
            if 'contract_data' in context:
                contract = context['contract_data']
                if contract.get('cpf') and extracted.get('cpf') == 'N/A':
                    extracted['cpf'] = contract.get('cpf', 'N/A')
                if contract.get('email') and extracted.get('email') == 'N/A':
                    extracted['email'] = contract.get('email', 'N/A')
                if contract.get('telefone') and extracted.get('telefone') == 'N/A':
                    extracted['telefone'] = contract.get('telefone', 'N/A')
                extracted['contrato_assinado'] = contract.get('contrato_assinado', 'N/A')
        else:
            # Direct access (fallback)
            extracted['stage'] = data.get('stage', 'N/A')
            if 'lead_data' in data:
                lead = data['lead_data']
                extracted['nome_cliente'] = lead.get('nome_cliente', 'N/A')
                extracted['tipo_interesse'] = lead.get('tipo_interesse', 'N/A')
                extracted['tipo_negocio'] = lead.get('tipo_negocio', 'N/A')

        # Remove N/A values for cleaner display
        extracted = {k: v for k, v in extracted.items() if v != 'N/A' and v is not None}

        return extracted

    except Exception as e:
        return {'error': str(e)}

def display_session(session, compact=False):
    """Display a single session in a readable format."""
    session_id, user_id, session_data, workflow_data, created_at, updated_at, workflow_name = session

    if compact:
        # Compact format for streaming updates
        print(f"📝 {session_id} | {format_timestamp(updated_at)}")
        conv_data = extract_conversation_data(session_data)
        if conv_data:
            # Show only key fields in one line
            key_info = []
            for key, value in conv_data.items():
                if key in ['stage', 'nome_cliente', 'nome_completo', 'tipo_interesse', 'contrato_assinado']:
                    key_info.append(f"{key}: {value}")
            if key_info:
                print(f"   {' | '.join(key_info)}")
        print()
    else:
        # Full format
        print("=" * 80)
        print(f"SESSION: {session_id}")
        print(f"User ID: {user_id}")
        print(f"Workflow: {workflow_name}")
        print(f"Created: {format_timestamp(created_at)} | Updated: {format_timestamp(updated_at)}")
        print("-" * 40)

        # Extract and display conversation data
        conv_data = extract_conversation_data(session_data)
        if conv_data:
            print("CONVERSATION DATA:")
            for key, value in conv_data.items():
                print(f"  {key}: {value}")

        print("-" * 40)
        print("RAW SESSION DATA:")
        print(format_json(session_data, 200))
        print()

def monitor_conversations():
    """Main monitoring loop."""
    print("🔍 CONVERSATION DATA MONITOR")
    print("=" * 80)
    print("Monitoring real-time conversation data...")
    print("Press Ctrl+C to stop")
    print()

    # Show initial state
    print("📊 CURRENT ACTIVE SESSIONS:")
    print("-" * 50)
    initial_sessions = get_latest_sessions(limit=5)
    if initial_sessions:
        for session in initial_sessions:
            display_session(session, compact=True)
    else:
        print("No active sessions found.")

    print("\n🔄 WAITING FOR NEW UPDATES...")
    print("=" * 80)

    last_update_time = max(session[5] for session in initial_sessions if session[5]) if initial_sessions else 0
    displayed_sessions = set()  # Track which sessions we've already displayed

    # Mark initial sessions as displayed
    for session in initial_sessions:
        session_id, user_id, session_data, workflow_data, created_at, updated_at, workflow_name = session
        session_key = f"{session_id}_{updated_at}"
        displayed_sessions.add(session_key)

    try:
        while True:
            # Get latest sessions
            sessions = get_latest_sessions(limit=10)  # Get more sessions to catch updates

            if sessions:
                # Check for new or updated sessions
                new_updates = []
                for session in sessions:
                    session_id, user_id, session_data, workflow_data, created_at, updated_at, workflow_name = session
                    session_key = f"{session_id}_{updated_at}"

                    # If this is a new session or an updated session we haven't shown yet
                    if session_key not in displayed_sessions and updated_at > last_update_time:
                        new_updates.append(session)
                        displayed_sessions.add(session_key)

                # Display new updates at the bottom
                if new_updates:
                    print(f"\n🔄 NEW UPDATE - {datetime.now().strftime('%H:%M:%S')}")
                    print("-" * 50)

                    for session in new_updates:
                        display_session(session, compact=True)

                    # Update last update time
                    latest_update = max(session[5] for session in sessions if session[5])
                    last_update_time = latest_update

                    # Clean up old displayed sessions to prevent memory buildup
                    if len(displayed_sessions) > 50:
                        # Keep only the most recent 30 session keys
                        recent_sessions = sorted(displayed_sessions)[-30:]
                        displayed_sessions = set(recent_sessions)

            time.sleep(2)  # Check every 2 seconds

    except KeyboardInterrupt:
        print("\n👋 Monitoring stopped.")

def show_current_data():
    """Show current data without monitoring loop."""
    print("📊 CURRENT CONVERSATION DATA")
    print("=" * 80)

    sessions = get_latest_sessions(limit=5)

    if not sessions:
        print("No conversation sessions found.")
        return

    for session in sessions:
        display_session(session)

def show_session_details(session_id):
    """Show detailed information about a specific session."""
    try:
        conn = sqlite3.connect("chat_history.db")
        cursor = conn.cursor()

        cursor.execute("""
            SELECT session_id, user_id, session_data, workflow_data,
                   created_at, updated_at, workflow_name
            FROM workflow_sessions_v2
            WHERE session_id = ?
        """, (session_id,))

        session = cursor.fetchone()
        conn.close()

        if not session:
            print(f"❌ Session '{session_id}' not found.")
            return

        print(f"🔍 DETAILED SESSION VIEW: {session_id}")
        print("=" * 80)
        display_session(session, compact=False)

    except Exception as e:
        print(f"Error retrieving session details: {e}")

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == "--current":
            show_current_data()
        elif sys.argv[1] == "--session" and len(sys.argv) > 2:
            show_session_details(sys.argv[2])
        elif sys.argv[1] == "--help":
            print("🔍 CONVERSATION DATA MONITOR")
            print("=" * 50)
            print("Usage:")
            print("  python monitor_conversations.py                    # Live monitoring")
            print("  python monitor_conversations.py --current          # Show current data")
            print("  python monitor_conversations.py --session <id>     # Show session details")
            print("  python monitor_conversations.py --help             # Show this help")
            print()
            print("Live monitoring shows new updates below previous ones and scrolls automatically.")
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Use --help for usage information.")
    else:
        monitor_conversations()
