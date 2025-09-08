from fastapi import FastAPI, Request
from agno.agent import Agent
from app.telegram.bot import TelegramBot
from app.telegram.config import TELEGRAM_BOT_TOKEN
import asyncio

app = FastAPI()
telegram_bot = TelegramBot(token=TELEGRAM_BOT_TOKEN)


# Exemplo de agente simples usando Agno
class EchoAgent(Agent):
    def run(self, message: str, **kwargs):
        return f"Agno respondeu: {message}"

agno_agent = EchoAgent()

@app.on_event('startup')
async def startup_event():
    loop = asyncio.get_event_loop()
    loop.create_task(telegram_bot.run_async())

@app.get('/')
def read_root():
    return {'message': 'API está rodando!'}


# Endpoint de chat usando o agente Agno
@app.post("/chat")
async def chat_endpoint(request: Request):
    data = await request.json()
    user_message = data.get("message")
    response = agno_agent.run(user_message)
    return {"response": response}
