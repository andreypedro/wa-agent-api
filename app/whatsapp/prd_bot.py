import logging
import os
from typing import Dict, Any, List
from dotenv import load_dotenv

from app.workflows.prd_workflow import get_prd_generation_workflow

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WhatsAppClient:
    """WhatsApp Business API client for PRD generation."""
    
    def __init__(self, access_token: str, phone_number_id: str):
        self.access_token = access_token
        self.phone_number_id = phone_number_id
        self.base_url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
        
    async def send_message(self, to: str, message: str) -> Dict[str, Any]:
        """Send a text message via WhatsApp Business API."""
        import aiohttp
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        payload = {
            'messaging_product': 'whatsapp',
            'to': to,
            'type': 'text',
            'text': {'body': message}
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(self.base_url, json=payload, headers=headers) as response:
                    result = await response.json()
                    
                    if response.status == 200:
                        logger.info(f"Message sent successfully to {to}")
                        return {'success': True, 'data': result}
                    else:
                        logger.error(f"Failed to send message: {result}")
                        return {'success': False, 'error': result}
                        
        except Exception as e:
            logger.error(f"Error sending WhatsApp message: {e}")
            return {'success': False, 'error': str(e)}


class PRDWhatsAppBot:
    """WhatsApp bot for PRD generation."""
    
    def __init__(self, access_token: str, phone_number_id: str, webhook_verify_token: str, app_secret: str):
        self.client = WhatsAppClient(access_token, phone_number_id)
        self.webhook_verify_token = webhook_verify_token
        self.app_secret = app_secret
        
    def verify_webhook(self, mode: str, token: str, challenge: str) -> str:
        """Verify webhook for WhatsApp."""
        if mode == "subscribe" and token == self.webhook_verify_token:
            logger.info("Webhook verified successfully")
            return challenge
        else:
            logger.warning("Webhook verification failed")
            return ""
    
    async def handle_webhook(self, data: Dict[str, Any]) -> Dict[str, str]:
        """Handle incoming WhatsApp webhook data."""
        try:
            if 'entry' not in data:
                return {'status': 'no_entry'}
            
            for entry in data['entry']:
                if 'changes' in entry:
                    for change in entry['changes']:
                        if change.get('field') == 'messages':
                            await self._handle_messages(change.get('value', {}))
            
            return {'status': 'success'}
            
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return {'status': 'error', 'message': str(e)}
    
    async def _handle_messages(self, value: Dict[str, Any]):
        """Handle incoming messages from WhatsApp."""
        try:
            messages = value.get('messages', [])
            
            for message in messages:
                await self._handle_single_message(message, value)
                
        except Exception as e:
            logger.error(f"Error handling messages: {str(e)}")
    
    async def _handle_single_message(self, message: Dict[str, Any], value: Dict[str, Any]):
        """Handle a single WhatsApp message for PRD generation."""
        try:
            from_number = message.get('from')
            message_id = message.get('id')
            timestamp = message.get('timestamp')
            message_type = message.get('type')
            
            logger.info(f"[WHATSAPP] Received {message_type} message from {from_number}")
            
            if message_type == 'text':
                text_content = message.get('text', {}).get('body', '').strip()
                
                if text_content:
                    logger.info(f"[WHATSAPP] Message from {from_number}: {text_content}")

                    # Create unified session ID (can be resumed on Telegram)
                    session_id = f"whatsapp_{from_number}"

                    # Process with PRD workflow
                    workflow = get_prd_generation_workflow(session_id=session_id)

                    # Process with workflow
                    workflow_output = workflow.run(text_content)
                    responses = []
                    if workflow_output and hasattr(workflow_output, 'content'):
                        responses.append(workflow_output.content)
                    elif workflow_output and hasattr(workflow_output, 'output'):
                        responses.append(str(workflow_output.output))

                    # Send response back
                    if responses:
                        # Join multiple responses if any
                        final_response = '\n\n'.join(responses)
                        
                        # Add progress indicator for WhatsApp
                        completion = workflow.get_completion_percentage()
                        if completion > 0 and completion < 100:
                            final_response += f"\n\n📊 Progress: {completion}%"

                        logger.info(f"[WHATSAPP] Generated response for {from_number}")

                        result = await self.client.send_message(from_number, final_response)

                        if not result.get('success'):
                            logger.error(f"Failed to send WhatsApp response: {result.get('error')}")
                        else:
                            logger.info(f"[WHATSAPP] Response sent to {from_number}: {final_response[:100]}...")
                    else:
                        # Fallback if no response generated
                        fallback_msg = "I'm sorry, I didn't understand that. Could you please tell me more about your software product idea?"
                        await self.client.send_message(from_number, fallback_msg)
            
            elif message_type in ['image', 'audio', 'video', 'document']:
                # Handle media messages with a simple response
                media_response = (
                    "🤖 I received your file, but I can only process text messages for PRD generation. "
                    "Please describe your software product idea in text so I can help you create a comprehensive PRD!"
                )
                await self.client.send_message(from_number, media_response)
                
            else:
                logger.info(f"[WHATSAPP] Unsupported message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling single message: {str(e)}")
    
    async def send_welcome_message(self, to: str):
        """Send welcome message to new WhatsApp user."""
        welcome_msg = (
            "🤖 Hello! Welcome to the PRD Generator!\n\n"
            "I'm your AI Product Manager assistant. I'll help you create a comprehensive "
            "Product Requirements Document (PRD) for your software product.\n\n"
            "Here's how I can help:\n"
            "📋 Gather your product requirements\n"
            "👥 Define your target audience\n"
            "⚙️ Identify technical specifications\n"
            "📊 Set success metrics\n"
            "📄 Generate a comprehensive PRD\n\n"
            "Just tell me about your software product idea and we'll get started!\n\n"
            "The process typically takes 15-30 minutes depending on complexity."
        )

        await self.client.send_message(to, welcome_msg)

    async def send_status_message(self, to: str, session_id: str):
        """Send current PRD generation status to user."""
        try:
            workflow = get_prd_generation_workflow(session_id=session_id)
            context_data = workflow.get_context()
            
            if context_data:
                completion = workflow.get_completion_percentage()
                phase = context_data.phase.value.replace('_', ' ').title()
                
                status_msg = (
                    f"📊 PRD Generation Status\n\n"
                    f"Current Phase: {phase}\n"
                    f"Progress: {completion}%\n"
                    f"Total Interactions: {context_data.total_interactions}\n\n"
                )
                
                if context_data.product_data.product_name:
                    status_msg += f"Product: {context_data.product_data.product_name}\n\n"
                
                if completion == 100:
                    status_msg += "🎉 Your PRD is complete!"
                else:
                    status_msg += "Continue our conversation to progress through the next phases."
                    
            else:
                status_msg = (
                    "📋 No active PRD generation session found.\n\n"
                    "Start by telling me about your software product idea!"
                )
            
            await self.client.send_message(to, status_msg)
            
        except Exception as e:
            logger.error(f"Error sending status: {e}")
            error_msg = "Sorry, there was an error getting your status. Please try again."
            await self.client.send_message(to, error_msg)

    async def handle_command(self, command: str, from_number: str):
        """Handle special commands from WhatsApp users."""
        session_id = f"whatsapp_{from_number}"
        
        if command.lower() in ['status', 'progress']:
            await self.send_status_message(from_number, session_id)
        elif command.lower() in ['help', 'start']:
            await self.send_welcome_message(from_number)
        elif command.lower() in ['reset', 'restart']:
            # Reset session and send welcome
            try:
                from app.core.database import get_workflow_storage
                storage = get_workflow_storage()
                if storage:
                    storage.delete_session(session_id)
                
                reset_msg = (
                    "🔄 Your PRD generation session has been reset!\n\n"
                    "You can now start fresh with a new product idea.\n"
                    "Tell me about your software product and we'll begin creating your PRD!"
                )
                await self.client.send_message(from_number, reset_msg)
            except Exception as e:
                logger.error(f"Error resetting session: {e}")
                await self.client.send_message(from_number, 
                    "Sorry, there was an error resetting your session. Please try again.")
        else:
            help_msg = (
                "🤖 Available commands:\n\n"
                "• 'help' or 'start' - Get started\n"
                "• 'status' or 'progress' - Check progress\n"
                "• 'reset' or 'restart' - Start over\n\n"
                "Or just tell me about your software product idea!"
            )
            await self.client.send_message(from_number, help_msg)


def create_whatsapp_bot():
    """Factory function to create and configure the WhatsApp bot."""
    access_token = os.getenv('WHATSAPP_ACCESS_TOKEN')
    phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID')
    webhook_verify_token = os.getenv('WHATSAPP_WEBHOOK_VERIFY_TOKEN')
    app_secret = os.getenv('WHATSAPP_APP_SECRET')
    
    if not all([access_token, phone_number_id, webhook_verify_token, app_secret]):
        raise ValueError("All WhatsApp environment variables are required")
    
    return PRDWhatsAppBot(access_token, phone_number_id, webhook_verify_token, app_secret)


# Global bot instance
whatsapp_bot = None

def get_whatsapp_bot():
    """Get or create WhatsApp bot instance."""
    global whatsapp_bot
    if whatsapp_bot is None:
        whatsapp_bot = create_whatsapp_bot()
    return whatsapp_bot
