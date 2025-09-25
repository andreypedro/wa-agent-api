import logging
import os
import hashlib
import hmac
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from app.workflows.lead_workflow import get_lead_conversion_workflow
from app.whatsapp.client import WhatsAppClient
from app.whatsapp.config import WHATSAPP_APP_SECRET, WHATSAPP_WEBHOOK_VERIFY_TOKEN

load_dotenv()

logger = logging.getLogger(__name__)

class AgnoWhatsAppBot:
    def __init__(self):
        # Initialize WhatsApp client
        self.client = WhatsAppClient()
    
    def verify_webhook_signature(self, payload: bytes, signature: str) -> bool:
        """Verify webhook signature for security"""
        if not WHATSAPP_APP_SECRET:
            logger.warning("WHATSAPP_APP_SECRET not configured - skipping signature verification")
            return True
            
        try:
            # Remove 'sha256=' prefix if present
            if signature.startswith('sha256='):
                signature = signature[7:]
            
            # Calculate expected signature
            expected_signature = hmac.new(
                WHATSAPP_APP_SECRET.encode('utf-8'),
                payload,
                hashlib.sha256
            ).hexdigest()
            
            # Secure comparison
            return hmac.compare_digest(expected_signature, signature)
            
        except Exception as e:
            logger.error(f"Error verifying webhook signature: {str(e)}")
            return False
    
    def verify_webhook_token(self, token: str) -> bool:
        """Verify webhook verification token"""
        return token == WHATSAPP_WEBHOOK_VERIFY_TOKEN
    
    async def handle_webhook_verification(self, verify_token: str, challenge: str) -> Optional[str]:
        """Handle webhook verification challenge"""
        if self.verify_webhook_token(verify_token):
            logger.info("Webhook verification successful")
            return challenge
        else:
            logger.warning("Webhook verification failed - invalid token")
            return None
    
    async def process_webhook_message(self, webhook_data: Dict[str, Any]) -> bool:
        """Process incoming webhook message from WhatsApp"""
        try:
            entries = webhook_data.get('entry', [])
            
            for entry in entries:
                changes = entry.get('changes', [])
                
                for change in changes:
                    if change.get('field') == 'messages':
                        messages = change.get('value', {}).get('messages', [])
                        
                        for message in messages:
                            await self._handle_single_message(message, change.get('value', {}))
            
            return True
            
        except Exception as e:
            logger.error(f"Error processing webhook message: {str(e)}")
            return False
    
    async def _handle_single_message(self, message: Dict[str, Any], message_data: Dict[str, Any]):
        """Handle a single message from WhatsApp"""
        try:
            message_id = message.get('id')
            from_number = message.get('from')
            message_type = message.get('type')
            timestamp = message.get('timestamp')
            
            # Mark message as read
            self.client.mark_message_as_read(message_id)
            
            # Only handle text messages for now
            if message_type == 'text':
                text_content = message.get('text', {}).get('body', '')
                
                if text_content:
                    logger.info(f"[WHATSAPP] Message from {from_number}: {text_content}")

                    # Create unified session ID (can be resumed on Telegram)
                    session_id = f"whatsapp_{from_number}"

                    # Process with workflow
                    workflow = get_lead_conversion_workflow(session_id=session_id)

                    # Collect responses
                    responses = []
                    for workflow_response in workflow.run(text_content):
                        if workflow_response.content:
                            responses.append(workflow_response.content)

                    # Send response back
                    if responses:
                        # Join multiple responses if any
                        final_response = '\n\n'.join(responses)

                        logger.info(f"[WHATSAPP] Generated response for {from_number}")

                        result = await self.client.send_message(from_number, final_response)

                        if result.get('error'):
                            logger.error(f"Failed to send WhatsApp response: {result['error']}")
                        else:
                            logger.info(f"[WHATSAPP] Response sent to {from_number}: {final_response[:100]}...")
                    else:
                        # Fallback if no response generated
                        fallback_msg = "Desculpe, não consegui processar sua mensagem. Pode tentar reformular?"
                        await self.client.send_message(from_number, fallback_msg)
            
            elif message_type in ['image', 'audio', 'video', 'document']:
                # Handle media messages with a simple response
                media_response = "🤖 Recebi seu arquivo, mas no momento só posso processar mensagens de texto. Por favor, descreva como posso ajudar você!"
                await self.client.send_message(from_number, media_response)
                
            else:
                logger.info(f"[WHATSAPP] Unsupported message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling single message: {str(e)}")
    
    async def send_welcome_message(self, to: str):
        """Send welcome message to new WhatsApp user"""
        welcome_msg = (
            "🤖 Olá! Bem-vindo!\n\n"
            "Sou uma assistente virtual e estou aqui para ajudar.\n\n"
            "Como posso ajudar você hoje?"
        )

        await self.client.send_message(to, welcome_msg)
    
    async def send_help_message(self, to: str):
        """Send help message with usage examples"""
        help_msg = (
            "🆘 *Como usar:*\n\n"
            "Sou uma assistente virtual pronta para conversar!\n\n"
            "Pode conversar comigo normalmente sobre qualquer assunto.\n\n"
            "Como posso ajudar você hoje?"
        )

        await self.client.send_message(to, help_msg)