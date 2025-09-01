
import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from app.core.openrouter_client import ask_openrouter

load_dotenv()

TELEGRAM_WELCOME = 'Bem-vindo! Como posso ajudar?'
SYSTEM_PROMPT = (
    'Você é uma assistente da Agilize Contabilidade Online. Responda sempre em português (PT-BR), de forma breve e direta, como se estivesse digitando pelo celular. '
    'Use as funções disponíveis para emitir, buscar ou cancelar notas fiscais, e nunca invente dados ao retornar resultados dessas funções. '
    'Execute a ação solicitada e retorne o resultado ao usuário, sem prometer nada. '
    'Se não puder realizar uma ação, explique de forma clara e educada. '
    'Quando precisar executar uma função, sempre retorne no formato JSON: {"function_call": {"name": "nome_funcao", "parameters": { ... }}}. Nunca invente dados e nunca mude esse formato.'
    'Funções disponíveis e parâmetros:'
    '\n- emitir_nfse(dados: {nome, valor, descricao, cnae, item_servico})'
    '\n- buscar_nfse(id_nfse, numero, nome, status)'
    '\n- cancelar_nfse(id_nfse, numero)'
)


OPENROUTER_MODEL = 'google/gemini-flash-1.5'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        os.environ['OPENROUTER_MODEL'] = OPENROUTER_MODEL
        self.application = ApplicationBuilder().token(token).build()
        self._setup_handlers()

    def _setup_handlers(self):
        self.application.add_handler(CommandHandler('start', self.start))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(TELEGRAM_WELCOME)

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        print(f"Mensagem recebida do usuário: {user_message}")
        response = ask_openrouter(user_message, SYSTEM_PROMPT)
        if not response or not response.strip():
            response = 'Desculpe, não consegui gerar uma resposta.'
        await update.message.reply_text(response)

    def run(self):
        self.application.run_polling()

    async def run_async(self):
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
