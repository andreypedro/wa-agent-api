import json

def process_response(response: str):
   """
   Limpa o retorno, identifica se é JSON ou texto.
   Se for texto, retorna o texto limpo.
   Se for JSON com função, executa a função correspondente.
   Suporta também o padrão function_call usado pelo modelo.
   """
   cleaned = response.strip()
   # Remove blocos de código markdown
   cleaned = cleaned.replace('```json', '').replace('```', '')
   # Se houver múltiplas linhas, processa cada uma
   lines = [line for line in cleaned.splitlines() if line.strip()]
   results = []
   for line in lines:
      try:
         data = json.loads(line)
         fc = None
         if isinstance(data, dict):
            if 'function_call' in data:
               fc = data['function_call']
            elif 'function' in data:
               fc = {'name': data['function'], 'parameters': data.get('args', {})}
         if fc and isinstance(fc, dict) and 'name' in fc and 'parameters' in fc:
            results.append(execute_function_from_json(fc))
         else:
            results.append(data)
      except Exception:
         # Não é JSON, retorna texto limpo
         results.append(line)
   # Retorna lista se múltiplos, ou único se só um
   if len(results) == 1:
      return results[0]
   return results

def execute_function_from_json(fc: dict):
   """
   Executa função baseada no dict {'name': ..., 'parameters': ...}
   """
   func_name = fc.get('name')
   params = fc.get('parameters', {})
   try:
      if func_name == 'emitir_nfse':
         from app.agents.nfse_agent import emitir_nfse
         return emitir_nfse(params)
      elif func_name == 'buscar_nfse':
         from app.agents.nfse_agent import buscar_nfse
         return buscar_nfse(params)
      elif func_name == 'cancelar_nfse':
         from app.agents.nfse_agent import cancelar_nfse
         return cancelar_nfse(params)
      elif func_name == 'get_all_nfse':
         from app.agents.nfse_agent import get_all_nfse
         return get_all_nfse(params)
      elif func_name == 'exemplo':
         return exemplo_funcao(**params)
      else:
         return f"Função '{func_name}' não implementada."
   except Exception as func_err:
      return f"Function call error: {func_name} - {func_err}"

def exemplo_funcao(**kwargs):
   # Exemplo de função chamada via JSON
   return f"Função exemplo chamada com argumentos: {kwargs}"
import os
import re
from dotenv import load_dotenv
from langchain.tools import Tool
from langchain_openai import ChatOpenAI

load_dotenv()

OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'openrouter/auto')
OPENROUTER_TOKEN = os.getenv('OPENROUTER_TOKEN')

from app.agents.nfse_agent import emitir_nfse, buscar_nfse, cancelar_nfse, get_all_nfse

def ask_openrouter(user_message: str, system_prompt: str = None) -> str:
   """
   Envia uma mensagem para o modelo via OpenRouter usando LangChain ChatOpenAI.
   Retorna o texto tratado por process_response.
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
      # Extrai o conteúdo da resposta
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

      return process_response(content)
   except Exception as e:
      return f"Erro LangChain: {str(e)}"