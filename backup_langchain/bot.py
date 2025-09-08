
import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from app.core.openrouter_client import ask_openrouter
from app.agents.nfse_agent import emitir_nfse, buscar_nfse, cancelar_nfse, get_all_nfse

load_dotenv()

TELEGRAM_WELCOME = 'Bem-vindo! Como posso ajudar?'
def get_functions_prompt():
   functions = [
      {
         "name": "emitir_nfse",
         "params": emitir_nfse.__annotations__
      },
      {
         "name": "buscar_nfse",
         "params": buscar_nfse.__annotations__
      },
      {
         "name": "cancelar_nfse",
         "params": cancelar_nfse.__annotations__
      },
      {
         "name": "get_all_nfse",
         "params": get_all_nfse.__annotations__
      }
   ]
   prompt = (
      'Você é uma assistente da Agilize Contabilidade Online. Responda sempre em português (PT-BR), de forma breve e direta, como se estivesse digitando pelo celular. '
      'Use as funções disponíveis para emitir, buscar ou cancelar notas fiscais, e nunca invente dados ao retornar resultados dessas funções. '
      'Execute a ação solicitada e retorne o resultado ao usuário, sem prometer nada. '
      'Se não puder realizar uma ação, explique de forma clara e educada. '
      'Quando precisar executar uma função, sempre retorne no formato JSON: {"function_call": {"name": "nome_funcao", "parameters": { ... }}}. Nunca invente dados e nunca mude esse formato.'
      'Funções disponíveis e parâmetros:\n'
   )
   for func in functions:
      params = ', '.join(func["params"].keys())
      prompt += f'- {func["name"]}({params})\n'
   return prompt

SYSTEM_PROMPT = get_functions_prompt()


OPENROUTER_MODEL = 'google/gemini-flash-1.5'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class TelegramBot:
    def __init__(self, token: str):
        self.token = token
        os.environ['OPENROUTER_MODEL'] = OPENROUTER_MODEL
        # Configure timeout settings for M4 Mac Docker environment
        self.application = (ApplicationBuilder()
                          .token(token)
                          .connect_timeout(10.0)  # Increase connect timeout
                          .read_timeout(20.0)     # Increase read timeout  
                          .write_timeout(20.0)    # Increase write timeout
                          .build())
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
        # Se for lista, junta os itens em uma string
        if isinstance(response, list):
            response = '\n'.join(str(item) for item in response)
        if not response or (isinstance(response, str) and not response.strip()):
            response = 'Desculpe, não consegui gerar uma resposta.'
        await update.message.reply_text(response)

    def run(self):
        self.application.run_polling()

    async def run_async(self):
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
