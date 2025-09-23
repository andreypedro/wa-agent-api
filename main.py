from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
import os
import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from app.workflows.lead_workflow import get_lead_conversion_workflow
from app.models.lead_models import ChatRequest, ChatResponse, ConversationContext

app = FastAPI(title="Lead Conversion API with Agno", version="2.0.0")

# Initialize bots based on environment variables
ENABLE_TELEGRAM = os.getenv('ENABLE_TELEGRAM', 'false').lower() == 'true'
ENABLE_WHATSAPP = os.getenv('ENABLE_WHATSAPP', 'false').lower() == 'true'

# Initialize Telegram bot
if ENABLE_TELEGRAM:
    from app.telegram.agno_bot import AgnoTelegramBot as TelegramBot
    from app.telegram.config import TELEGRAM_BOT_TOKEN
    telegram_bot = TelegramBot(token=TELEGRAM_BOT_TOKEN)

# Initialize WhatsApp bot
if ENABLE_WHATSAPP:
    from app.whatsapp.agno_bot import AgnoWhatsAppBot
    whatsapp_bot = AgnoWhatsAppBot()

@app.on_event('startup')
async def startup_event():
    if ENABLE_TELEGRAM:
        loop = asyncio.get_event_loop()
        loop.create_task(telegram_bot.run_async())
    # WhatsApp bot runs via webhooks, no startup task needed

@app.get('/')
def read_root():
    return {
        'message': 'Lead Conversion API com Agno está rodando!',
        'framework': 'Agno',
        'model': 'google/gemini-2.5-flash via OpenRouter',
        'features': ['Lead Conversion State Machine', 'Brazilian Accounting Services', 'Multi-channel Support'],
        'workflow_stages': [
            'inicial',
            'qualificacao',
            'proposta',
            'contratacao',
            'coleta_documentos_pessoais',
            'definicao_empresa',
            'escolha_cnae',
            'endereco_comercial',
            'revisao_final',
            'processamento',
            'concluido',
            'pausado',
            'abandonado'
        ],
        'qualification_threshold': 'R$ 5.000/mês',
        'channels': {
            'telegram': ENABLE_TELEGRAM,
            'whatsapp': ENABLE_WHATSAPP
        },
        'endpoints': {
            'chat': '/chat',
            'session': '/session/{session_id}',
            'health': '/health'
        }
    }

@app.get('/health')
def health_check():
    return {
        'status': 'healthy',
        'framework': 'agno',
        'workflow': 'lead_conversion',
        'channels': {
            'telegram_enabled': ENABLE_TELEGRAM,
            'whatsapp_enabled': ENABLE_WHATSAPP
        }
    }

@app.post('/chat', response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint for testing the lead conversion workflow.
    """
    try:
        print(f"[API] Received request: message='{request.message}', session_id='{request.session_id}'")

        # Generate session ID if not provided
        session_id = request.session_id or f"api_{datetime.now().timestamp()}"

        # Create workflow instance
        print(f"[API] Creating workflow with session_id: {session_id}")
        workflow = get_lead_conversion_workflow(session_id=session_id)

        # Process message
        responses = []
        for workflow_response in workflow.run(request.message):
            if workflow_response.content:
                responses.append(workflow_response.content)

        # Get context for response metadata
        context = workflow._get_context()

        return ChatResponse(
            session_id=session_id,
            responses=responses,
            stage=context.stage.value,
            qualified=context.is_qualified if context.lead_data.renda_mensal else None,
            qualification_reason=context.qualification_reason,
            context={
                'turns': context.conversation_turns,
                'fields_collected': context.fields_collected,
                'income': context.lead_data.renda_mensal,
                'name': context.lead_data.nome_completo,
                'email': context.lead_data.email
            }
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")

@app.get('/session/{session_id}')
async def get_session_info(session_id: str):
    """
    Get session information and current state.
    """
    try:
        workflow = get_lead_conversion_workflow(session_id=session_id)
        context = workflow._get_context()

        return {
            'session_id': session_id,
            'stage': context.stage.value,
            'conversation_turns': context.conversation_turns,
            'qualified': context.is_qualified,
            'qualification_reason': context.qualification_reason,
            'session_expired': context.is_session_expired(),
            'lead_data': context.lead_data.model_dump(exclude_none=True),
            'fields_collected': context.fields_collected,
            'messages_count': len(context.messages_exchanged)
        }

    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Sessão não encontrada: {str(e)}")

@app.delete('/session/{session_id}')
async def reset_session(session_id: str):
    """
    Reset/clear a session.
    """
    try:
        workflow = get_lead_conversion_workflow(session_id=session_id)
        workflow.reset()

        return {
            'session_id': session_id,
            'status': 'reset',
            'message': 'Sessão reiniciada com sucesso'
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao resetar sessão: {str(e)}")

# WhatsApp webhook endpoints
if ENABLE_WHATSAPP:
    @app.get('/webhooks/whatsapp')
    async def whatsapp_webhook_verify(request: Request):
        """Verify WhatsApp webhook"""
        verify_token = request.query_params.get('hub.verify_token')
        challenge = request.query_params.get('hub.challenge')
        mode = request.query_params.get('hub.mode')
        
        if mode == 'subscribe':
            result = await whatsapp_bot.handle_webhook_verification(verify_token, challenge)
            if result:
                return PlainTextResponse(result)
            else:
                raise HTTPException(status_code=403, detail="Forbidden")
        
        raise HTTPException(status_code=400, detail="Bad Request")
    
    @app.post('/webhooks/whatsapp')
    async def whatsapp_webhook_receive(request: Request):
        """Receive WhatsApp webhook messages"""
        try:
            # # Get raw body for signature verification
            body = await request.body()
            # signature = request.headers.get('x-hub-signature-256', '')
            
            # # Verify signature
            # if not whatsapp_bot.verify_webhook_signature(body, signature):
            #     raise HTTPException(status_code=403, detail="Invalid signature")
            
            # Parse JSON data
            webhook_data = json.loads(body)
            
            # Process the webhook message
            success = await whatsapp_bot.process_webhook_message(webhook_data)
            
            if success:
                return {"status": "success"}
            else:
                raise HTTPException(status_code=500, detail="Processing failed")
                
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
