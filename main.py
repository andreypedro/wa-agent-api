from fastapi import FastAPI
import os
import asyncio

app = FastAPI(title="Agilize NFSe API with Agno", version="1.0.0")

# Only initialize Telegram bot if enabled
ENABLE_TELEGRAM = os.getenv('ENABLE_TELEGRAM', 'false').lower() == 'true'

if ENABLE_TELEGRAM:
    from app.telegram.agno_bot import AgnoTelegramBot as TelegramBot
    from app.telegram.config import TELEGRAM_BOT_TOKEN
    telegram_bot = TelegramBot(token=TELEGRAM_BOT_TOKEN)

@app.on_event('startup')
async def startup_event():
    if ENABLE_TELEGRAM:
        loop = asyncio.get_event_loop()
        loop.create_task(telegram_bot.run_async())

@app.get('/')
def read_root():
    return {
        'message': 'Agilize NFSe API com Agno está rodando!',
        'framework': 'Agno',
        'model': 'google/gemini-2.5-flash via OpenRouter',
        'features': ['NFSe Operations', 'Conversation Memory', 'Tool Integration']
    }

@app.get('/health')
def health_check():
    return {
        'status': 'healthy',
        'framework': 'agno',
        'telegram_enabled': ENABLE_TELEGRAM
    }
