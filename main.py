from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
import os
import asyncio
import json
from datetime import datetime
from typing import Dict, Any

from app.workflows.prd_workflow import get_prd_generation_workflow
from app.models.prd_models import ChatRequest, ChatResponse

app = FastAPI(title="PRD Generator API", version="2.0.0")

# Initialize bots based on environment variables
ENABLE_TELEGRAM = os.getenv('ENABLE_TELEGRAM', 'false').lower() == 'true'
ENABLE_WHATSAPP = os.getenv('ENABLE_WHATSAPP', 'false').lower() == 'true'

# Initialize Telegram bot
if ENABLE_TELEGRAM:
    from app.telegram.prd_bot import PRDTelegramBot as TelegramBot
    telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
    if telegram_bot_token:
        telegram_bot = TelegramBot(token=telegram_bot_token)
    else:
        print("Warning: TELEGRAM_BOT_TOKEN not configured")
        telegram_bot = None

# Initialize WhatsApp bot
if ENABLE_WHATSAPP:
    from app.whatsapp.prd_bot import get_whatsapp_bot
    try:
        whatsapp_bot = get_whatsapp_bot()
    except ValueError as e:
        print(f"Warning: WhatsApp bot configuration error: {e}")
        whatsapp_bot = None

@app.on_event('startup')
async def startup_event():
    if ENABLE_TELEGRAM and telegram_bot:
        print("Starting PRD Telegram Bot...")
        loop = asyncio.get_event_loop()
        loop.create_task(asyncio.to_thread(telegram_bot.run))
    # WhatsApp bot runs via webhooks, no startup task needed

@app.get('/')
def read_root():
    return {
        'message': 'PRD Generator API is running!',
        'framework': 'Agno',
        'model': 'google/gemini-2.5-flash via OpenRouter',
        'features': ['PRD Generation Workflow', 'AI Product Manager', 'Multi-channel Support'],
        'workflow_phases': [
            'initial_discovery',
            'product_vision',
            'target_audience',
            'core_features',
            'user_stories',
            'technical_requirements',
            'success_metrics',
            'constraints_assumptions',
            'prd_review',
            'prd_refinement',
            'prd_finalization',
            'completed',
            'paused',
            'abandoned'
        ],
        'purpose': 'Generate comprehensive Product Requirements Documents for software products',
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
        'workflow': 'prd_generation',
        'channels': {
            'telegram_enabled': ENABLE_TELEGRAM,
            'whatsapp_enabled': ENABLE_WHATSAPP
        }
    }

@app.post('/chat', response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    """
    Main chat endpoint for PRD generation workflow.
    """
    try:
        print(f"[API] Received request: message='{request.message}', session_id='{request.session_id}'")

        # Generate session ID if not provided
        session_id = request.session_id or f"prd_{datetime.now().timestamp()}"

        # Create workflow instance
        print(f"[API] Creating PRD workflow with session_id: {session_id}")
        workflow = get_prd_generation_workflow(session_id=session_id)

        # Process message
        workflow_output = workflow.run(request.message)
        responses = []
        if workflow_output and hasattr(workflow_output, 'content'):
            responses.append(workflow_output.content)
        elif workflow_output and hasattr(workflow_output, 'output'):
            responses.append(str(workflow_output.output))

        # Get current context for response metadata
        context = workflow.get_context()
        current_phase = context.phase.value if context else "unknown"
        completion_percentage = workflow.get_completion_percentage() if hasattr(workflow, 'get_completion_percentage') else 0

        print(f"[API] Generated {len(responses)} responses for phase: {current_phase}")

        return ChatResponse(
            session_id=session_id,
            responses=responses,
            phase=current_phase,
            completion_percentage=completion_percentage,
            generated_prd=context.generated_prd if context else None,
            context={
                'phase': current_phase,
                'completion_percentage': completion_percentage,
                'total_interactions': getattr(context, 'total_interactions', 0) if context else 0,
                'created_at': getattr(context, 'created_at', None) if context else None,
            }
        )

    except Exception as e:
        print(f"[API] Error processing request: {str(e)}")
        import traceback
        traceback.print_exc()

        # Return error response
        return ChatResponse(
            session_id=request.session_id or "error",
            responses=[f"Sorry, an error occurred while processing your message: {str(e)}"],
            phase="error",
            context={'error': str(e)}
        )

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
