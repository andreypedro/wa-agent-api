import logging
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from agno.agent import Agent
from agno.models.openrouter import OpenRouter

from app.agents.nfse_agno_tools import (
    emitir_nfse_tool, 
    buscar_nfse_tool, 
    cancelar_nfse_tool, 
    get_all_nfse_tool
)

load_dotenv()

TELEGRAM_WELCOME = 'Bem-vindo! Como posso ajudar você hoje?'

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class AgnoTelegramBot:
    def __init__(self, token: str):
        self.token = token
        
        # Initialize Agno agent with OpenRouter
        self.agent = Agent(
            name="Assistente Agilize NFSe",
            agent_id="agilize_nfse_bot",
            model=OpenRouter(
                id="google/gemini-2.5-flash",
                api_key=os.getenv('OPENROUTER_TOKEN')
            ),
            tools=[
                emitir_nfse_tool,
                buscar_nfse_tool,
                cancelar_nfse_tool,
                get_all_nfse_tool
            ],
            instructions=[
                "Você é uma assistente especializada da Agilize Contabilidade Online.",
                "Responda sempre em português (PT-BR), de forma breve e direta, como se estivesse digitando pelo celular.",
                
                # INTELIGÊNCIA PROATIVA - BUSQUE DADOS ANTES DE PERGUNTAR
                "IMPORTANTE: Antes de pedir dados ao usuário, SEMPRE tente buscar informações existentes:",
                "1. Quando o usuário mencionar 'como a última nota', 'igual a anterior', 'para o mesmo cliente', 'repetir', PRIMEIRO use get_all_nfse_tool ou buscar_nfse_tool",
                "2. Analise os resultados para extrair dados similares (cliente, valores, descrições, CNAE, item_servico)",
                "3. Use esses dados como base para novas operações",
                "4. SÓ pergunte ao usuário dados que NÃO conseguir encontrar nas notas existentes",
                
                # FLUXOS DE TRABALHO INTELIGENTES
                "FLUXO PARA 'CRIAR NOTA COMO A ÚLTIMA PARA [CLIENTE]':",
                "→ 1) buscar_nfse_tool(nome=[CLIENTE]) para encontrar notas do cliente",
                "→ 2) Extrair dados da nota mais recente (valor, descrição, CNAE, item_servico)", 
                "→ 3) emitir_nfse_tool usando dados encontrados",
                
                "FLUXO PARA 'NOTA IGUAL À ANTERIOR/ÚLTIMA':",
                "→ 1) get_all_nfse_tool() para encontrar a nota mais recente",
                "→ 2) MOSTRAR APENAS A ÚLTIMA NOTA encontrada (não uma lista)",
                "→ 3) Usar formato de confirmação estruturado (ver abaixo)",
                "→ 4) Aguardar confirmação do usuário antes de emitir",
                
                # FORMATO DE CONFIRMAÇÃO ESTRUTURADO
                "QUANDO MOSTRAR DADOS PARA CONFIRMAÇÃO, use este formato EXATO:",
                "📄 **Dados da última nota encontrada:**",
                "👤 Cliente: [NOME]",
                "💰 Valor: R$ [VALOR]", 
                "📋 Descrição: [DESCRIÇÃO]",
                "🏢 CNAE: [CNAE]",
                "🔧 Item serviço: [ITEM]",
                "",
                "✅ Confirma emissão com esses dados? (Responda 'sim', 'confirmar' ou 'ok')",
                
                # REGRAS DE VERBOSIDADE
                "IMPORTANTE - SEJA CONCISO:",
                "• Para 'última nota': mostre APENAS 1 nota (a mais recente)",
                "• Para 'cliente específico': mostre APENAS a nota mais recente desse cliente", 
                "• Nunca mostre listas longas quando o usuário pede 'a última' ou 'igual à anterior'",
                "• Use o formato estruturado acima para confirmações",
                
                # REGRAS DE FERRAMENTAS
                "SEMPRE use as funções disponíveis quando o usuário solicitar operações de NFSe:",
                "• get_all_nfse_tool: Use para contexto geral, 'última nota', 'últimas notas'",
                "• buscar_nfse_tool: Use para cliente específico ou critérios específicos",
                "• emitir_nfse_tool: Use APENAS depois de ter todos os dados (de busca OU usuário)",
                "• cancelar_nfse_tool: Use para cancelamentos",
                
                # COMPORTAMENTO
                "NUNCA invente dados - use apenas o que encontrar nas buscas ou o que o usuário fornecer explicitamente.",
                "Execute múltiplas ferramentas em sequência quando necessário para completar a tarefa.",
                "Seja proativo em buscar dados, mas transparente sobre o que encontrou.",
                "SEMPRE use o formato de confirmação estruturado definido acima - nunca pergunte de forma solta."
            ],
            markdown=True,
            add_history_to_messages=True,
            num_history_responses=5,
            show_tool_calls=False,  # Hide internal tool calls from user
            add_datetime_to_instructions=True,
            debug_mode=False
        )
        
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
            "Sou sua assistente da Agilize Contabilidade!\n\n"
            "Posso ajudar você com:\n"
            "📄 Emitir notas fiscais\n"
            "🔍 Buscar notas existentes\n"
            "📋 Listar suas notas\n"
            "🚫 Cancelar notas fiscais\n\n"
            "Digite /help para ver exemplos de comandos."
        )
        await update.message.reply_text(welcome_msg)

    async def help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        help_msg = (
            "🆘 **Como usar:**\n\n"
            "**Para emitir nota fiscal:**\n"
            "• \"Emitir nota para João Silva no valor de R$ 1000\"\n"
            "• \"Criar NFS-e para Maria Santos, serviço de consultoria\"\n\n"
            "**Para buscar notas:**\n"
            "• \"Buscar notas do cliente João\"\n"
            "• \"Procurar nota número 123\"\n\n"
            "**Para listar notas:**\n"
            "• \"Mostrar minhas últimas notas\"\n"
            "• \"Listar todas as notas\"\n\n"
            "**Para cancelar:**\n"
            "• \"Cancelar nota 123\"\n"
            "• \"Cancelar NFS-e ID abc123\"\n\n"
            "**Comandos:**\n"
            "• /reset - Limpar histórico da conversa"
        )
        await update.message.reply_text(help_msg, parse_mode='Markdown')

    async def reset_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Reset conversation memory for current user"""
        user_id = str(update.effective_user.id)
        # For now, just inform user (memory will be added later)
        await update.message.reply_text("🔄 Comando reset recebido. Conversas futuras serão tratadas como novas.")

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_message = update.message.text
        user_id = str(update.effective_user.id)
        
        print(f"[AGNO] Mensagem recebida do usuário {user_id}: {user_message}")
        
        try:
            # Use Agno agent with user context and memory - this will automatically
            # decide when to use tools based on the user's request
            response = await self.agent.arun(
                message=user_message,
                user_id=user_id,
                session_id=f"telegram_{user_id}"
            )
            
            # Extract response content from Agno agent response
            if hasattr(response, 'content'):
                response_text = response.content
            elif hasattr(response, 'messages') and response.messages:
                # Handle case where response has messages array
                response_text = response.messages[-1].get('content', str(response))
            else:
                response_text = str(response)
            
            # Validate response
            if not response_text or (isinstance(response_text, str) and not response_text.strip()):
                response_text = 'Desculpe, não consegui gerar uma resposta. Pode tentar reformular sua pergunta?'
            
            # Log tools usage for debugging
            if hasattr(response, 'tool_calls') and response.tool_calls:
                tool_names = [tool.get('name', 'unknown') for tool in response.tool_calls]
                print(f"[AGNO] Ferramentas usadas pelo agente: {', '.join(tool_names)}")
            
            print(f"[AGNO] Resposta enviada para usuário {user_id}: {response_text[:100]}...")
            
            # Try to send with Markdown first, fallback to plain text if parsing fails
            try:
                await update.message.reply_text(response_text, parse_mode='Markdown')
            except Exception as parse_error:
                print(f"[AGNO] Markdown parsing failed, sending as plain text: {parse_error}")
                await update.message.reply_text(response_text)
            
        except Exception as e:
            logging.error(f"[AGNO] Error processing message from user {user_id}: {str(e)}")
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