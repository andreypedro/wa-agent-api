import logging
import os
import tempfile
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from app.workflows.prd_workflow import get_prd_generation_workflow
from app.models.prd_models import ConversationContext
from app.core.database import get_workflow_storage
try:
    from app.services.audio_transcription import get_transcription_service, AudioTranscriptionError
    AUDIO_TRANSCRIPTION_AVAILABLE = True
    print("[TELEGRAM] Audio transcription available with Groq API")
except ImportError as e:
    print(f"[TELEGRAM] Audio transcription not available - voice messages will be disabled: {e}")
    AUDIO_TRANSCRIPTION_AVAILABLE = False
    AudioTranscriptionError = Exception
    get_transcription_service = None

load_dotenv()

TELEGRAM_WELCOME = 'Hello! I\'m your AI Product Manager assistant. I\'ll help you create a comprehensive Product Requirements Document for your software product idea.'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class PRDTelegramBot:
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
        self.application.add_handler(CommandHandler('status', self.status))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))
        # Add voice message handler if transcription is available
        if AUDIO_TRANSCRIPTION_AVAILABLE:
            self.application.add_handler(MessageHandler(filters.VOICE, self.handle_voice_message))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        welcome_msg = (
            f"🤖 {TELEGRAM_WELCOME}\n\n"
            "Olá! Sou seu assistente especializado em criar Documentos de Requisitos de Produto (PRD) para produtos de software!\n\n"
            "Como posso te ajudar:\n"
            "📋 Coletar os requisitos do seu produto\n"
            "👥 Definir seu público-alvo\n"
            "⚙️ Identificar especificações técnicas\n"
            "📊 Estabelecer métricas de sucesso\n"
            "📄 Gerar um PRD abrangente\n\n"
            "Apenas me conte sobre sua ideia de produto de software e vamos começar!\n\n"
            "Digite /help para ver os comandos disponíveis."
        )
        await update.message.reply_text(welcome_msg)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_msg = (
            "🤖 Comandos do Bot Gerador de PRD:\n\n"
            "/start - Iniciar uma nova sessão de geração de PRD\n"
            "/help - Mostrar esta mensagem de ajuda\n"
            "/reset - Limpar histórico da conversa e recomeçar\n"
            "/status - Verificar progresso atual e fase\n\n"
            "💡 Dicas:\n"
            f"{'• Você pode enviar mensagens de voz - eu vou transcrevê-las!' if AUDIO_TRANSCRIPTION_AVAILABLE else '• Envie mensagens de texto com suas ideias de produto'}\n"
            "• Seja o mais detalhado possível sobre sua ideia de produto\n"
            "• Vou te guiar através de cada fase da coleta de requisitos\n"
            "• O processo normalmente leva 15-30 minutos dependendo da complexidade\n\n"
            "Apenas comece me contando sobre sua ideia de produto de software!"
        )
        await update.message.reply_text(help_msg)

    async def reset_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reset conversation memory for the user."""
        try:
            user_id = str(update.effective_user.id)
            session_id = f"telegram_{user_id}"
            
            # Clear workflow storage for this session
            storage = get_workflow_storage()
            if storage:
                # Clear the session data
                storage.delete_session(session_id)
            
            reset_msg = (
                "🔄 Sua sessão de geração de PRD foi reiniciada!\n\n"
                "Agora você pode começar do zero com uma nova ideia de produto.\n"
                "Me conte sobre seu produto de software e vamos começar a criar seu PRD!"
            )
            await update.message.reply_text(reset_msg)
            
        except Exception as e:
            logging.error(f"Error resetting memory: {e}")
            await update.message.reply_text(
                "Desculpe, houve um erro ao reiniciar sua sessão. Tente novamente ou entre em contato com o suporte."
            )

    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show current PRD generation status and progress."""
        try:
            user_id = str(update.effective_user.id)
            session_id = f"telegram_{user_id}"
            
            # Get current workflow state
            workflow = get_prd_generation_workflow(session_id=session_id)
            context_data = workflow.get_context()
            
            if context_data:
                completion = workflow.get_completion_percentage()
                phase = context_data.phase.value.replace('_', ' ').title()
                
                status_msg = (
                    f"📊 Status da Geração de PRD\n\n"
                    f"Fase Atual: {phase}\n"
                    f"Progresso: {completion}%\n"
                    f"Total de Interações: {context_data.total_interactions}\n"
                    f"Iniciado: {context_data.created_at.strftime('%d/%m/%Y %H:%M') if context_data.created_at else 'Desconhecido'}\n\n"
                )
                
                if context_data.product_data.product_name:
                    status_msg += f"Produto: {context_data.product_data.product_name}\n"

                if completion == 100:
                    status_msg += "🎉 Seu PRD está completo!"
                else:
                    status_msg += "Continue nossa conversa para progredir através das próximas fases."

            else:
                status_msg = (
                    "📋 Nenhuma sessão ativa de geração de PRD encontrada.\n\n"
                    "Comece me contando sobre sua ideia de produto de software!"
                )
            
            await update.message.reply_text(status_msg)
            
        except Exception as e:
            logging.error(f"Error getting status: {e}")
            await update.message.reply_text(
                "Desculpe, houve um erro ao obter seu status. Tente novamente."
            )

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages for PRD generation."""
        try:
            user_id = str(update.effective_user.id)
            user_message = update.message.text
            session_id = f"telegram_{user_id}"

            logging.info(f"[TELEGRAM] Message from {user_id}: {user_message}")

            # Create workflow instance
            workflow = get_prd_generation_workflow(session_id=session_id)

            # Process message and collect responses
            workflow_output = workflow.run(user_message)
            responses = []
            if workflow_output and hasattr(workflow_output, 'content'):
                responses.append(workflow_output.content)
            elif workflow_output and hasattr(workflow_output, 'output'):
                responses.append(str(workflow_output.output))

            # Send response back to user
            if responses:
                # Join multiple responses if any
                final_response = '\n\n'.join(responses)
                
                # Add progress indicator
                completion = workflow.get_completion_percentage()
                if completion > 0 and completion < 100:
                    final_response += f"\n\n📊 Progresso: {completion}%"
                
                await update.message.reply_text(final_response)
                logging.info(f"[TELEGRAM] Response sent to {user_id}")
            else:
                # Fallback if no response generated
                fallback_msg = "Desculpe, não entendi. Você poderia reformular ou fornecer mais detalhes sobre seu produto de software?"
                await update.message.reply_text(fallback_msg)

        except Exception as e:
            logging.error(f"Error handling message: {str(e)}")
            error_msg = "Desculpe, encontrei um erro ao processar sua mensagem. Tente novamente ou digite /reset para recomeçar."
            await update.message.reply_text(error_msg)

    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages by transcribing them first."""
        if not AUDIO_TRANSCRIPTION_AVAILABLE:
            await update.message.reply_text(
                "🎤 Mensagens de voz não são suportadas nesta configuração. Por favor, envie uma mensagem de texto."
            )
            return

        try:
            user_id = str(update.effective_user.id)
            logging.info(f"[TELEGRAM] Voice message from {user_id}")

            # Get the voice file
            voice_file = await update.message.voice.get_file()

            # Download to temporary file
            with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as temp_file:
                await voice_file.download_to_drive(temp_file.name)
                temp_path = temp_file.name

            try:
                # Transcribe the audio
                transcription_service = get_transcription_service()
                transcribed_text = transcription_service.transcribe_audio(
                    temp_path,
                    language="pt",  # Portuguese for Brazilian users
                    prompt="Product requirements and software development discussion"
                )
                
                if transcribed_text:
                    logging.info(f"[TELEGRAM] Transcribed voice from {user_id}: {transcribed_text}")
                    
                    # Send transcription confirmation
                    await update.message.reply_text(f"🎤 Ouvi: \"{transcribed_text}\"\n\nProcessando sua mensagem...")
                    
                    # Process the transcribed text as a regular message
                    session_id = f"telegram_{user_id}"
                    workflow = get_prd_generation_workflow(session_id=session_id)

                    workflow_output = workflow.run(transcribed_text)
                    responses = []
                    if workflow_output and hasattr(workflow_output, 'content'):
                        responses.append(workflow_output.content)
                    elif workflow_output and hasattr(workflow_output, 'output'):
                        responses.append(str(workflow_output.output))

                    if responses:
                        final_response = '\n\n'.join(responses)
                        
                        # Add progress indicator
                        completion = workflow.get_completion_percentage()
                        if completion > 0 and completion < 100:
                            final_response += f"\n\n📊 Progresso: {completion}%"
                        
                        await update.message.reply_text(final_response)
                    else:
                        await update.message.reply_text(
                            "Transcrevi sua mensagem de voz mas não consegui processá-la. Você poderia tentar novamente?"
                        )
                else:
                    await update.message.reply_text(
                        "🎤 Não consegui transcrever sua mensagem de voz claramente. Tente novamente ou envie uma mensagem de texto."
                    )

            except AudioTranscriptionError as e:
                logging.error(f"Transcription error: {e}")
                await update.message.reply_text(
                    "🎤 Desculpe, tive problemas para transcrever sua mensagem de voz. Tente enviar uma mensagem de texto."
                )
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass

        except Exception as e:
            logging.error(f"Error handling voice message: {str(e)}")
            await update.message.reply_text(
                "Desculpe, encontrei um erro ao processar sua mensagem de voz. Tente enviar uma mensagem de texto."
            )

    def run(self):
        """Start the bot."""
        logging.info("Starting PRD Telegram Bot...")
        self.application.run_polling()


def create_telegram_bot():
    """Factory function to create and configure the Telegram bot."""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    
    return PRDTelegramBot(token)


if __name__ == '__main__':
    bot = create_telegram_bot()
    bot.run()
