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
            "I'm here to guide you through creating a Product Requirements Document (PRD) for your software product!\n\n"
            "Here's how I can help:\n"
            "📋 Gather your product requirements\n"
            "👥 Define your target audience\n"
            "⚙️ Identify technical specifications\n"
            "📊 Set success metrics\n"
            "📄 Generate a comprehensive PRD\n\n"
            "Just tell me about your software product idea and we'll get started!\n\n"
            "Type /help to see available commands."
        )
        await update.message.reply_text(welcome_msg)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_msg = (
            "🤖 PRD Generator Bot Commands:\n\n"
            "/start - Start a new PRD generation session\n"
            "/help - Show this help message\n"
            "/reset - Clear conversation history and start over\n"
            "/status - Check current progress and phase\n\n"
            "💡 Tips:\n"
            f"{'• You can send voice messages - I will transcribe them!' if AUDIO_TRANSCRIPTION_AVAILABLE else '• Send text messages with your product ideas'}\n"
            "• Be as detailed as possible about your product idea\n"
            "• I'll guide you through each phase of requirement gathering\n"
            "• The process typically takes 15-30 minutes depending on complexity\n\n"
            "Just start by telling me about your software product idea!"
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
                "🔄 Your PRD generation session has been reset!\n\n"
                "You can now start fresh with a new product idea.\n"
                "Tell me about your software product and we'll begin creating your PRD!"
            )
            await update.message.reply_text(reset_msg)
            
        except Exception as e:
            logging.error(f"Error resetting memory: {e}")
            await update.message.reply_text(
                "Sorry, there was an error resetting your session. Please try again or contact support."
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
                    f"📊 PRD Generation Status\n\n"
                    f"Current Phase: {phase}\n"
                    f"Progress: {completion}%\n"
                    f"Total Interactions: {context_data.total_interactions}\n"
                    f"Started: {context_data.created_at.strftime('%Y-%m-%d %H:%M') if context_data.created_at else 'Unknown'}\n\n"
                )
                
                if context_data.product_data.product_name:
                    status_msg += f"Product: {context_data.product_data.product_name}\n"
                
                if completion == 100:
                    status_msg += "🎉 Your PRD is complete!"
                else:
                    status_msg += "Continue our conversation to progress through the next phases."
                    
            else:
                status_msg = (
                    "📋 No active PRD generation session found.\n\n"
                    "Start by telling me about your software product idea!"
                )
            
            await update.message.reply_text(status_msg)
            
        except Exception as e:
            logging.error(f"Error getting status: {e}")
            await update.message.reply_text(
                "Sorry, there was an error getting your status. Please try again."
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
                    final_response += f"\n\n📊 Progress: {completion}%"
                
                await update.message.reply_text(final_response)
                logging.info(f"[TELEGRAM] Response sent to {user_id}")
            else:
                # Fallback if no response generated
                fallback_msg = "I'm sorry, I didn't understand that. Could you please rephrase or provide more details about your software product?"
                await update.message.reply_text(fallback_msg)

        except Exception as e:
            logging.error(f"Error handling message: {str(e)}")
            error_msg = "Sorry, I encountered an error processing your message. Please try again or type /reset to start over."
            await update.message.reply_text(error_msg)

    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages by transcribing them first."""
        if not AUDIO_TRANSCRIPTION_AVAILABLE:
            await update.message.reply_text(
                "🎤 Voice messages are not supported in this configuration. Please send a text message instead."
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
                    language="en",  # Changed to English for PRD generation
                    prompt="Product requirements and software development discussion"
                )
                
                if transcribed_text:
                    logging.info(f"[TELEGRAM] Transcribed voice from {user_id}: {transcribed_text}")
                    
                    # Send transcription confirmation
                    await update.message.reply_text(f"🎤 I heard: \"{transcribed_text}\"\n\nProcessing your message...")
                    
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
                            final_response += f"\n\n📊 Progress: {completion}%"
                        
                        await update.message.reply_text(final_response)
                    else:
                        await update.message.reply_text(
                            "I transcribed your voice message but couldn't process it. Could you please try again?"
                        )
                else:
                    await update.message.reply_text(
                        "🎤 I couldn't transcribe your voice message clearly. Please try again or send a text message."
                    )

            except AudioTranscriptionError as e:
                logging.error(f"Transcription error: {e}")
                await update.message.reply_text(
                    "🎤 Sorry, I had trouble transcribing your voice message. Please try sending a text message instead."
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
                "Sorry, I encountered an error processing your voice message. Please try sending a text message."
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
