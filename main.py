from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import PlainTextResponse
import os
import asyncio
import json
from typing import Dict, Any

app = FastAPI(title="Agilize NFSe API with Agno", version="1.0.0")

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
        'message': 'Agilize NFSe API com Agno está rodando!',
        'framework': 'Agno',
        'model': 'google/gemini-2.5-flash via OpenRouter',
        'features': ['NFSe Operations', 'Conversation Memory', 'Tool Integration'],
        'channels': {
            'telegram': ENABLE_TELEGRAM,
            'whatsapp': ENABLE_WHATSAPP
        }
    }

@app.get('/health')
def health_check():
    return {
        'status': 'healthy',
        'framework': 'agno',
        'channels': {
            'telegram_enabled': ENABLE_TELEGRAM,
            'whatsapp_enabled': ENABLE_WHATSAPP
        }
    }

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
            # Get raw body for signature verification
            body = await request.body()
            signature = request.headers.get('x-hub-signature-256', '')
            
            # Verify signature
            if not whatsapp_bot.verify_webhook_signature(body, signature):
                raise HTTPException(status_code=403, detail="Invalid signature")
            
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
