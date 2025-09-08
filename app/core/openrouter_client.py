
# Refatoração para uso do framework Agno
import os
from dotenv import load_dotenv
from agno.agent import Agent
from app.agents.nfse_agent import emitir_nfse, buscar_nfse, cancelar_nfse, get_all_nfse

load_dotenv()

class NFSeAgent(Agent):
   def run(self, message: str, **kwargs):
      """
      Processa a mensagem do usuário e executa funções NFSe conforme solicitado.
      """
      # Aqui você pode adicionar parsing, validação, etc.
      # Exemplo: comandos simples
      if message.lower().startswith("emitir nfse"):
         # Espera-se que os parâmetros venham após o comando
         # Exemplo: "emitir nfse nome=João valor=1000 descricao=Consultoria cnae=1234 item_servico=01.01"
         params = self._parse_params(message)
         return emitir_nfse(params)
      elif message.lower().startswith("buscar nfse"):
         params = self._parse_params(message)
         return buscar_nfse(params)
      elif message.lower().startswith("cancelar nfse"):
         params = self._parse_params(message)
         return cancelar_nfse(params)
      elif message.lower().startswith("listar nfse"):
         params = self._parse_params(message)
         return get_all_nfse(params)
      else:
         return "Comando não reconhecido. Tente: emitir nfse, buscar nfse, cancelar nfse ou listar nfse."

   def _parse_params(self, message: str):
      # Extrai parâmetros do texto (exemplo simples)
      import re
      pattern = r"(\w+)=([^ ]+)"
      matches = re.findall(pattern, message)
      return {k: v for k, v in matches}

# Instância do agente
nfse_agent = NFSeAgent()

def ask_agno(user_message: str) -> str:
   """
   Envia uma mensagem para o agente Agno e retorna a resposta.
   """
   try:
      return nfse_agent.run(user_message)
   except Exception as e:
      return f"Erro Agno: {str(e)}"