import requests
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from app.whatsapp.config import WHATSAPP_ACCESS_TOKEN, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_API_BASE_URL

logger = logging.getLogger(__name__)

class WhatsAppClient:
    def __init__(self):
        self.access_token = WHATSAPP_ACCESS_TOKEN
        self.phone_number_id = WHATSAPP_PHONE_NUMBER_ID
        self.base_url = WHATSAPP_API_BASE_URL
        self.session = requests.Session()
        
        # Rate limiting: WhatsApp allows 80 messages/second
        self.rate_limit_semaphore = asyncio.Semaphore(80)
        self.rate_limit_delay = 1.0  # 1 second window
        
    def _get_headers(self) -> Dict[str, str]:
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
    
    async def send_message(self, to: str, message: str, message_type: str = 'text') -> Dict[str, Any]:
        """Send a text message to WhatsApp user"""
        async with self.rate_limit_semaphore:
            try:
                url = f"{self.base_url}/{self.phone_number_id}/messages"

                print(f"Sending message to {url}")
                
                payload = {
                    "messaging_product": "whatsapp",
                    "to": to,
                    "type": message_type,
                    "text": {
                        "body": message
                    }
                }
                
                response = self.session.post(
                    url,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    logger.info(f"Message sent successfully to {to}")
                    return response.json()
                else:
                    logger.error(f"Failed to send message to {to}: {response.status_code} - {response.text}")
                    return {"error": f"HTTP {response.status_code}: {response.text}"}
                    
            except Exception as e:
                logger.error(f"Error sending WhatsApp message: {str(e)}")
                return {"error": str(e)}
            finally:
                # Rate limiting delay
                await asyncio.sleep(self.rate_limit_delay / 80)
    
    async def send_template_message(self, to: str, template_name: str, language: str = "pt_BR", 
                                  components: Optional[list] = None) -> Dict[str, Any]:
        """Send a template message (for marketing or notifications)"""
        async with self.rate_limit_semaphore:
            try:
                url = f"{self.base_url}/{self.phone_number_id}/messages"
                
                payload = {
                    "messaging_product": "whatsapp",
                    "to": to,
                    "type": "template",
                    "template": {
                        "name": template_name,
                        "language": {
                            "code": language
                        }
                    }
                }
                
                if components:
                    payload["template"]["components"] = components
                
                response = self.session.post(
                    url,
                    headers=self._get_headers(),
                    json=payload,
                    timeout=30
                )
                
                if response.status_code == 200:
                    logger.info(f"Template message sent successfully to {to}")
                    return response.json()
                else:
                    logger.error(f"Failed to send template to {to}: {response.status_code} - {response.text}")
                    return {"error": f"HTTP {response.status_code}: {response.text}"}
                    
            except Exception as e:
                logger.error(f"Error sending WhatsApp template: {str(e)}")
                return {"error": str(e)}
            finally:
                await asyncio.sleep(self.rate_limit_delay / 80)
    
    def mark_message_as_read(self, message_id: str) -> Dict[str, Any]:
        """Mark a received message as read"""
        try:
            url = f"{self.base_url}/{self.phone_number_id}/messages"
            
            payload = {
                "messaging_product": "whatsapp",
                "status": "read",
                "message_id": message_id
            }
            
            response = self.session.post(
                url,
                headers=self._get_headers(),
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug(f"Message {message_id} marked as read")
                return response.json()
            else:
                logger.warning(f"Failed to mark message as read: {response.status_code}")
                return {"error": f"HTTP {response.status_code}: {response.text}"}
                
        except Exception as e:
            logger.error(f"Error marking message as read: {str(e)}")
            return {"error": str(e)}
    
    def get_media(self, media_id: str) -> Optional[bytes]:
        """Download media file from WhatsApp"""
        try:
            # First get media URL
            url = f"{self.base_url}/{media_id}"
            response = self.session.get(url, headers=self._get_headers(), timeout=10)
            
            if response.status_code == 200:
                media_data = response.json()
                media_url = media_data.get('url')
                
                if media_url:
                    # Download the actual media file
                    media_response = self.session.get(
                        media_url, 
                        headers={'Authorization': f'Bearer {self.access_token}'},
                        timeout=30
                    )
                    
                    if media_response.status_code == 200:
                        return media_response.content
                    else:
                        logger.error(f"Failed to download media: {media_response.status_code}")
                        return None
            else:
                logger.error(f"Failed to get media URL: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error downloading media: {str(e)}")
            return None