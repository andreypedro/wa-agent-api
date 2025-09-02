import os
import re
from dotenv import load_dotenv
from langchain.tools import Tool
from langchain_openai import ChatOpenAI

load_dotenv()

OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'openrouter/auto')
OPENROUTER_TOKEN = os.getenv('OPENROUTER_TOKEN')

from app.agents.nfse_agent import emitir_nfse, buscar_nfse, cancelar_nfse

# Ferramentas para LangChain (podem ser usadas em fluxos customizados, LangGraph, etc)
emitir_nfse_tool = Tool(
   name="emitir_nfse",
   description="Emite uma nota fiscal de serviço (NFS-e). Espera um dict com os campos: nome, valor, descricao, cnae, item_servico.",
   func=emitir_nfse
)
buscar_nfse_tool = Tool(
   name="buscar_nfse",
   description="Busca uma nota fiscal de serviço (NFS-e) por filtros. Espera um dict com os campos: id_nfse, numero, nome, status.",
   func=buscar_nfse
)
cancelar_nfse_tool = Tool(
   name="cancelar_nfse",
   description="Cancela uma nota fiscal de serviço (NFS-e) pelo número ou id. Espera um dict com os campos: id_nfse, numero.",
   func=cancelar_nfse
)

def ask_openrouter(user_message: str, system_prompt: str = None) -> str:
   """
   Envia uma mensagem para o modelo via OpenRouter usando LangChain ChatOpenAI.
   Retorna apenas o texto gerado pela IA.
   """
   if not OPENROUTER_TOKEN:
      return 'Token OpenRouter não configurado.'

   llm = ChatOpenAI(
      openai_api_key=OPENROUTER_TOKEN,
      model_name=OPENROUTER_MODEL,
      openai_api_base="https://openrouter.ai/api/v1"
   )

   messages = []
   if system_prompt:
      messages.append({"role": "system", "content": system_prompt})
   messages.append({"role": "user", "content": user_message})

   try:
      result = llm.invoke(messages)
      # Extrai conteúdo da resposta
      content = None
      if isinstance(result, dict):
         if 'choices' in result and isinstance(result['choices'], list):
            choice = result['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
               content = choice['message']['content']
         if not content and 'content' in result:
            content = result['content']
      elif isinstance(result, list) and len(result) > 0:
         if isinstance(result[-1], dict) and 'content' in result[-1]:
            content = result[-1]['content']
      elif hasattr(result, 'content'):
         content = result.content
      else:
         content = str(result)

      # Detecta e executa function_call
      import json
      try:
         content_json = json.loads(content)
         fc = content_json.get('function_call')
         if fc and isinstance(fc, dict) and 'name' in fc and 'parameters' in fc:
            func_name = fc['name']
            params = fc['parameters']
            if func_name == 'emitir_nfse':
               return emitir_nfse(params)
            elif func_name == 'buscar_nfse':
               return buscar_nfse(params)
            elif func_name == 'cancelar_nfse':
               return cancelar_nfse(params)
      except Exception:
         pass
      return content
   except Exception as e:
      return f"Erro LangChain: {str(e)}"