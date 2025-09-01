import os
import requests
import re
from dotenv import load_dotenv
from app.agents.definitions import get_emitir_nfse_function, get_buscar_nfse_function, get_cancelar_nfse_function

load_dotenv()

OPENROUTER_API_URL = 'https://openrouter.ai/api/v1/chat/completions'
OPENROUTER_MODEL = os.getenv('OPENROUTER_MODEL', 'openrouter/auto')
OPENROUTER_TOKEN = os.getenv('OPENROUTER_TOKEN')

def ask_openrouter(user_message: str, system_prompt: str = None) -> str:
    token = OPENROUTER_TOKEN
    if not token:
        return 'Token OpenRouter não configurado.'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    messages = []
    system_instruction = "Responda apenas com os dados solicitados, sem instruções de código ou exemplos de chamadas de função. Se for necessário chamar uma função, apenas retorne os dados."
    if system_prompt:
        messages.append({"role": "system", "content": system_instruction + " " + system_prompt})
    else:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": user_message})
    payload = {
        "model": OPENROUTER_MODEL,
        "messages": messages,
        "functions": [
            get_emitir_nfse_function(),
            get_buscar_nfse_function(),
            get_cancelar_nfse_function()
        ],
        "temperature": 0.1
    }

    response = requests.post(OPENROUTER_API_URL, headers=headers, json=payload)
    if response.status_code != 200:
        return f'Erro na chamada OpenRouter: {response.text}'
    data = response.json()
    choice = data.get('choices', [{}])[0]
    message = choice.get('message', {})

    import json
    content = message.get('content', '')

    def is_json(text):
        try:
            obj = json.loads(text)
            return obj
        except Exception:
            return None

    def execute_function_call(fc):
        if fc and isinstance(fc, dict) and 'name' in fc and 'parameters' in fc:
            function_name = fc['name']
            arguments = fc['parameters']
            if function_name == "emitir_nfse":
                from app.agents.nfse_agent import emitir_nfse
                result = emitir_nfse(arguments)
            elif function_name == "buscar_nfse":
                from app.agents.nfse_agent import buscar_nfse
                result = buscar_nfse(**arguments)
            elif function_name == "cancelar_nfse":
                from app.agents.nfse_agent import cancelar_nfse
                result = cancelar_nfse(**arguments)
            else:
                result = f"Função desconhecida: {function_name}"
            if isinstance(result, str):
                result = re.sub(r"print\\((.*?)\\)", r"\\1", result, flags=re.DOTALL)
            return result
        return None

    print(f"Resposta bruta do OpenRouter: {content}")

    content_json = is_json(content)
    if content_json:
        fc = content_json.get('function_call')
        result = execute_function_call(fc)
        if result is not None:
            return result
        else:
            return content_json
    else:
        return content