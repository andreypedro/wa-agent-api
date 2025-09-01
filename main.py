from fastapi import FastAPI

from app.telegram.bot import TelegramBot
from app.telegram.config import TELEGRAM_BOT_TOKEN
from fastapi import FastAPI
import asyncio

app = FastAPI()
telegram_bot = TelegramBot(token=TELEGRAM_BOT_TOKEN)

@app.on_event('startup')
async def startup_event():
    loop = asyncio.get_event_loop()
    loop.create_task(telegram_bot.run_async())

@app.get('/')
def read_root():
    return {'message': 'API está rodando!'}
