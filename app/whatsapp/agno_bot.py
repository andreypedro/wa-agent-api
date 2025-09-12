import logging
import os
import hashlib
import hmac
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.openrouter import OpenRouter

from app.agents.nfse_agno_tools import (
    emit_nfse_tool, 
    get_one_nfse_tool, 
    cancel_nfse_tool, 
    get_all_nfse_tool
)
from app.whatsapp.client import WhatsAppClient
from app.whatsapp.config import WHATSAPP_APP_SECRET, WHATSAPP_WEBHOOK_VERIFY_TOKEN

load_dotenv()

logger = logging.getLogger(__name__)

class AgnoWhatsAppBot:
    def __init__(self):
        # Initialize WhatsApp client
        self.client = WhatsAppClient()
        
        # Initialize Agno agent with same configuration as Telegram bot
        self.agent = Agent(
            name="Assistente Agilize NFSe WhatsApp",
            # agent_id="agilize_nfse_whatsapp_bot",
            model=OpenRouter(
                id="google/gemini-2.5-flash",
                api_key=os.getenv('OPENROUTER_TOKEN')
            ),
            tools=[
                emit_nfse_tool,
                get_one_nfse_tool,
                cancel_nfse_tool,
                get_all_nfse_tool
            ],
            instructions=[
                "Você é uma assistente especializada da Agilize Contabilidade Online.",
                "Responda sempre em português (PT-BR), de forma breve e direta, como se estivesse digitando pelo celular.",
                "Como você está no WhatsApp, mantenha as mensagens concisas e use emojis apropriados quando relevante.",
                
                # INTELIGÊNCIA PROATIVA - BUSQUE DADOS ANTES DE PERGUNTAR  
                "🔍 IMPORTANTE: Antes de pedir dados ao usuário, SEMPRE tente buscar informações existentes:",
                "1. Quando o usuário mencionar 'como a última nota', 'igual a anterior', 'para o mesmo cliente', 'repetir', PRIMEIRO use get_all_nfse_tool ou buscar_nfse_tool",
                "2. Analise os resultados para extrair dados similares (cliente, valores, descrições, CNAE, item_servico)",
                "3. Use esses dados como base para novas operações",
                "4. SÓ pergunte ao usuário dados que NÃO conseguir encontrar nas notas existentes",
                
                # FLUXOS DE TRABALHO INTELIGENTES
                "📋 FLUXO PARA 'CRIAR NOTA COMO A ÚLTIMA PARA [CLIENTE]':",
                "→ 1) get_one_nfse_tool(nome=[CLIENTE]) para encontrar notas do cliente",
                "→ 2) Extrair dados da nota mais recente (valor, descrição, CNAE, item_servico)", 
                "→ 3) emit_nfse_tool usando dados encontrados",
                
                "🔄 FLUXO PARA 'NOTA IGUAL À ANTERIOR/ÚLTIMA':",
                "→ 1) get_all_nfse_tool() para encontrar a nota mais recente",
                "→ 2) MOSTRAR APENAS A ÚLTIMA NOTA encontrada (não uma lista)",
                "→ 3) Usar formato de confirmação estruturado (ver abaixo)",
                "→ 4) Aguardar confirmação do usuário antes de emitir",
                
                # FORMATO DE CONFIRMAÇÃO ESTRUTURADO
                "📱 QUANDO MOSTRAR DADOS PARA CONFIRMAÇÃO, use este formato EXATO:",
                "📄 *Dados da última nota encontrada:*",
                "👤 Cliente: [NOME]",
                "💰 Valor: R$ [VALOR]", 
                "📋 Descrição: [DESCRIÇÃO]",
                "🏢 CNAE: [CNAE]",
                "🔧 Item serviço: [ITEM]",
                "",
                "✅ Confirma emissão com esses dados?",
                "(Responda 'sim', 'confirmar' ou 'ok')",
                
                # REGRAS DE VERBOSIDADE E FORMATO DE RESPOSTA
                "📝 IMPORTANTE - SEJA CONCISO E ESTRUTURADO:",
                "• Para 'última nota': mostre APENAS 1 nota (a mais recente)",
                "• Para 'cliente específico': mostre APENAS a nota mais recente desse cliente", 
                "• Nunca mostre listas longas quando o usuário pede 'a última' ou 'igual à anterior'",
                "• SEMPRE use o formato estruturado para confirmações - NUNCA responda de forma solta",
                "• NUNCA mostre dados brutos como 'Número: 2025002, Nome: Maria...' - sempre use o formato estruturado",
                "• Mantenha mensagens curtas e diretas (ideal para WhatsApp)",
                
                # REGRAS DE FERRAMENTAS
                "🛠️ SEMPRE use as funções disponíveis quando o usuário solicitar operações de NFSe:",
                "• get_all_nfse_tool: Use para contexto geral, 'última nota', 'últimas notas'",
                "• get_one_nfse_tool: Use para cliente específico ou critérios específicos",
                "• emit_nfse_tool: Use APENAS depois de ter todos os dados (de busca OU usuário)",
                "• cancel_nfse_tool: Use para cancelamentos",

                # GERENCIAMENTO DE CONTEXTO AVANÇADO
                "🧠 CONTEXT MANAGEMENT - CRÍTICO:",
                "1. PRESERVE informações do usuário durante toda a conversa (ex: se usuário disse 'valor é 3600', lembre disso)",
                "2. COMBINE dados do usuário com dados das buscas inteligentemente",
                "3. Quando usuário fornecer PARTE das informações, mantenha esses dados e busque o resto",
                "4. EXEMPLO: Usuário diz 'valor 3600' + 'copie dados da última nota' = Combine valor 3600 + outros dados da última nota",
                "5. NUNCA perca informações que o usuário já forneceu - sempre as preserve e combine",
                
                # COMPORTAMENTO
                "❗ NUNCA invente dados - use apenas o que encontrar nas buscas ou o que o usuário fornecer explicitamente.",
                "⚡ Execute múltiplas ferramentas em sequência quando necessário para completar a tarefa.",
                "🤖 Seja proativo em buscar dados, mas transparente sobre o que encontrou.",
                "✅ SEMPRE use o formato de confirmação estruturado definido acima - nunca pergunte de forma solta.",
                "🔄 Mantenha CONTINUIDADE CONTEXTUAL - lembre o que o usuário já disse na conversa atual."
            ],
            markdown=False,  # WhatsApp doesn't support markdown
            # add_history_to_messages=True,
            # num_history_responses=10,  # Increased for better context preservation
            # show_tool_calls=False,
            # add_datetime_to_instructions=True,
            debug_mode=False
        )
    
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
                    
                    # Process with Agno agent
                    response = await self.agent.arun(
                        input=text_content,
                        user_id=from_number,
                        session_id=f"whatsapp_{from_number}"
                    )
                    
                    # Extract response content
                    if hasattr(response, 'content'):
                        response_text = response.content
                    elif hasattr(response, 'messages') and response.messages:
                        response_text = response.messages[-1].get('content', str(response))
                    else:
                        response_text = str(response)
                    
                    # Validate response
                    if not response_text or (isinstance(response_text, str) and not response_text.strip()):
                        response_text = 'Desculpe, não consegui gerar uma resposta. Pode tentar reformular sua pergunta?'
                    
                    # Log tool usage
                    if hasattr(response, 'tool_calls') and response.tool_calls:
                        tool_names = [tool.get('name', 'unknown') for tool in response.tool_calls]
                        logger.info(f"[WHATSAPP] Tools used: {', '.join(tool_names)}")
                    
                    # Send response back
                    result = await self.client.send_message(from_number, response_text)
                    
                    if result.get('error'):
                        logger.error(f"Failed to send WhatsApp response: {result['error']}")
                    else:
                        logger.info(f"[WHATSAPP] Response sent to {from_number}: {response_text[:100]}...")
            
            elif message_type in ['image', 'audio', 'video', 'document']:
                # Handle media messages with a simple response
                media_response = "🤖 Recebi seu arquivo, mas no momento só posso processar mensagens de texto. Por favor, descreva como posso ajudar com as notas fiscais!"
                await self.client.send_message(from_number, media_response)
                
            else:
                logger.info(f"[WHATSAPP] Unsupported message type: {message_type}")
                
        except Exception as e:
            logger.error(f"Error handling single message: {str(e)}")
    
    async def send_welcome_message(self, to: str):
        """Send welcome message to new WhatsApp user"""
        welcome_msg = (
            "🤖 Bem-vindo à Agilize Contabilidade!\n\n"
            "Sou sua assistente para operações de NFSe.\n\n"
            "Posso ajudar com:\n"
            "📄 Emitir notas fiscais\n"
            "🔍 Buscar notas existentes\n" 
            "📋 Listar suas notas\n"
            "🚫 Cancelar notas fiscais\n\n"
            "Como posso ajudar você hoje?"
        )
        
        await self.client.send_message(to, welcome_msg)
    
    async def send_help_message(self, to: str):
        """Send help message with usage examples"""
        help_msg = (
            "🆘 *Como usar:*\n\n"
            "*Para emitir nota fiscal:*\n"
            "• \"Emitir nota para João Silva no valor de R$ 1000\"\n"
            "• \"Criar NFS-e para Maria Santos, serviço de consultoria\"\n\n"
            "*Para buscar notas:*\n"
            "• \"Buscar notas do cliente João\"\n"
            "• \"Procurar nota número 123\"\n\n"
            "*Para listar notas:*\n"
            "• \"Mostrar minhas últimas notas\"\n"
            "• \"Listar todas as notas\"\n\n"
            "*Para cancelar:*\n"
            "• \"Cancelar nota 123\"\n"
            "• \"Cancelar NFS-e ID abc123\""
        )
        
        await self.client.send_message(to, help_msg)