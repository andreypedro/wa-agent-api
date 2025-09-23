# 🔍 Real-time Conversation Data Monitor

Simple tool to see what data is being saved during user conversations in real time.

## Quick Start

### 1. View Current Data (One-time)
```bash
python monitor_conversations.py --current
```

### 2. Real-time Monitoring (Live Updates)
```bash
python monitor_conversations.py
```

### 3. View Specific Session Details
```bash
python monitor_conversations.py --session <session_id>
```

### 4. Show Help
```bash
python monitor_conversations.py --help
```

## What You'll See

### Live Console Output (from bot)
When users interact with the bot, you'll see real-time logs like:
```
💾 [DATA SAVED] Session: telegram_776451684
   Stage: qualificacao
   Nome: Rafael
   Interesse: primeira_empresa
   Negócio: servicos
```

### Monitor Interface
The monitor shows:
- **Initial State**: Current active sessions when starting
- **Live Updates**: New updates appear below previous ones (no screen clearing)
- **Compact Format**: New updates show key information in a condensed format
- **Session ID**: Unique identifier for each conversation
- **User ID**: Platform user ID (Telegram, WhatsApp)
- **Workflow**: Current workflow name
- **Timestamps**: When conversation started/last updated
- **Conversation Data**: Key extracted information
- **Raw Data**: Complete session data in JSON format (detailed view only)

### Example Output

#### Live Monitoring Mode
```
🔍 CONVERSATION DATA MONITOR
================================================================================
Monitoring real-time conversation data...
Press Ctrl+C to stop

📊 CURRENT ACTIVE SESSIONS:
--------------------------------------------------
📝 telegram_776451684 | 15:30:31
   stage: contratacao | nome_completo: Rafael Oliveira Viana | tipo_interesse: primeira_empresa | contrato_assinado: True

🔄 WAITING FOR NEW UPDATES...
================================================================================

🔄 NEW UPDATE - 15:32:15
--------------------------------------------------
📝 telegram_776451684 | 15:32:15
   stage: finalizacao | nome_completo: Rafael Oliveira Viana | contrato_assinado: True

🔄 NEW UPDATE - 15:35:22
--------------------------------------------------
📝 whatsapp_5511999887766 | 15:35:22
   stage: qualificacao | nome_cliente: Maria Silva | tipo_interesse: nova_empresa
```

#### Detailed View (--current or --session)
```
================================================================================
SESSION: telegram_776451684
User ID: None
Workflow: Agilize Onboarding State Machine
Created: 15:15:18 | Updated: 15:30:31
----------------------------------------
CONVERSATION DATA:
  stage: contratacao
  nome_completo: Rafael Oliveira Viana
  tipo_interesse: primeira_empresa
  tipo_negocio: servicos
  cpf: 031.898.095-93
  email: rafa.viana@gmail.com
  contrato_assinado: True
----------------------------------------
RAW SESSION DATA:
{
  "context": {
    "stage": "contratacao",
    "lead_data": {
      "nome_completo": "Rafael Oliveira Viana",
      "tipo_interesse": "primeira_empresa",
      ...
    }
  }
}
```

## Key Data Fields

### Lead Data
- `nome_cliente` / `nome_completo`: User's name
- `tipo_interesse`: Type of interest (primeira_empresa, nova_empresa, etc.)
- `tipo_negocio`: Business type (comercio, servicos, industria, misto)
- `estrutura_societaria`: Company structure (mei, socios, indefinido)
- `aceite_proposta`: Whether user accepted the proposal

### Contract Data
- `cpf`: User's CPF
- `email`: User's email
- `telefone`: User's phone
- `contrato_assinado`: Whether contract was signed

### Process Data
- `stage`: Current conversation stage
- `process_status`: Current process status

## Usage Tips

1. **Start monitoring before testing**: Run the monitor first, then interact with the bot
2. **Use --current for quick checks**: See current state without live monitoring
3. **Use --session <id> for details**: Get full details of a specific session
4. **Press Ctrl+C to stop**: Exit the live monitoring loop
5. **Check console logs**: Bot also prints data saves in real-time
6. **Automatic scrolling**: New updates appear below, terminal scrolls automatically
7. **Compact updates**: Live monitoring shows condensed format for easy scanning

## Files
- `monitor_conversations.py`: Main monitoring script
- `chat_history.db`: SQLite database with conversation data
- Bot console: Real-time data save notifications
