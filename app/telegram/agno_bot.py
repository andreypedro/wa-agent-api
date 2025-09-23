import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from app.workflows.lead_workflow import get_lead_conversion_workflow
from app.models.lead_models import ConversationContext
from app.core.database import get_workflow_storage

load_dotenv()

TELEGRAM_WELCOME = 'Olá! Sou sua assistente da Agilize Contabilidade. Como posso ajudar você hoje?'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class AgnoTelegramBot:
    def __init__(self, token: str):
        self.token = token
        
        # Configure timeout settings for M4 Mac Docker environment
        self.application = (ApplicationBuilder()
                          .token(token)
                          .connect_timeout(10.0)
                          .read_timeout(20.0)
                          .write_timeout(20.0)
                          .build())
        self._setup_handlers()

    def _setup_handlers(self):
        self.application.add_handler(CommandHandler('start', self.start))
        self.application.add_handler(CommandHandler('help', self.help))
        self.application.add_handler(CommandHandler('reset', self.reset_memory))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_msg = (
            f"🤖 {TELEGRAM_WELCOME}\n\n"
            "Somos especialistas em contabilidade para empreendedores brasileiros!\n\n"
            "Como posso ajudar você hoje?\n"
            "📊 Serviços de contabilidade\n"
            "📋 Abertura de empresa\n"
            "💰 Gestão fiscal\n"
            "📄 Declaração de imposto de renda\n\n"
            "Digite /help para ver os comandos disponíveis."
        )
        await update.message.reply_text(welcome_msg)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_msg = (
            "🆘 **Como usar:**\n\n"
            "Sou sua assistente da Agilize Contabilidade!\n\n"
            "**Comandos disponíveis:**\n"
            "• /start - Iniciar conversa\n"
            "• /help - Ver esta ajuda\n"
            "• /reset - Limpar histórico da conversa\n\n"
            "**Exemplos do que posso ajudar:**\n"
            "• 'Preciso de um contador'\n"
            "• 'Quero abrir uma empresa'\n"
            "• 'Ajuda com impostos'\n\n"
            "Pode conversar comigo normalmente!"
        )
        await update.message.reply_text(help_msg, parse_mode='Markdown')

    async def reset_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reset conversation memory for current user"""
        user_id = str(update.effective_user.id)
        session_id = f"telegram_{user_id}"

        try:
            workflow = get_lead_conversion_workflow(session_id=session_id)
            workflow.reset()

            storage = get_workflow_storage()
            if storage:
                storage.delete_session(session_id=session_id)

            print(f"[RESET] ✅ Cleared conversation history and persistent storage for user {user_id}")
            await update.message.reply_text(
                "🔄 **Histórico limpo!**\n\n"
                "Sua conversa foi completamente reiniciada. Vamos começar do zero!\n\n"
                "Como posso ajudar você hoje com nossos serviços de contabilidade?",
                parse_mode='Markdown'
            )

        except Exception as e:
            print(f"[RESET] Error clearing session for user {user_id}: {str(e)}")
            await update.message.reply_text(
                "🔄 **Histórico reiniciado!**\n\n"
                "Sua conversa foi reiniciada. Como posso ajudar você hoje?",
                parse_mode='Markdown'
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        user_id = str(update.effective_user.id)
        session_id = f"telegram_{user_id}"

        print(f"[WORKFLOW] Mensagem recebida do usuário {user_id}: {user_message}")

        try:
            # Create workflow instance for this session
            workflow = get_lead_conversion_workflow(session_id=session_id)

            # Process message through workflow
            responses = []
            for workflow_response in workflow.run(user_input=user_message):
                if workflow_response.content:
                    responses.append(workflow_response.content)

            # Send all responses
            if responses:
                # Join multiple responses if any
                final_response = '\n\n'.join(responses)

                print(f"[WORKFLOW] Resposta enviada para usuário {user_id}: {final_response[:100]}...")

                # Try to send with Markdown first, fallback to plain text
                try:
                    await update.message.reply_text(final_response, parse_mode='Markdown')
                except Exception as parse_error:
                    print(f"[WORKFLOW] Markdown parsing failed, sending as plain text: {parse_error}")
                    await update.message.reply_text(final_response)
            else:
                # Fallback if no response generated
                fallback_msg = "Desculpe, não consegui processar sua mensagem. Pode tentar reformular?"
                await update.message.reply_text(fallback_msg)

        except Exception as e:
            logging.error(f"[WORKFLOW] Error processing message from user {user_id}: {str(e)}")
            error_msg = "❌ Ops! Ocorreu um erro ao processar sua mensagem. Tente novamente em alguns instantes."
            await update.message.reply_text(error_msg)

    def run(self):
        """Run the bot with polling"""
        self.application.run_polling()

    async def run_async(self):
        """Run the bot asynchronously"""
        await self.application.initialize()
        await self.application.start()
        await self.application.updater.start_polling()
