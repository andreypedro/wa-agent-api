import requests
import os

OLLAMA_API_URL = os.getenv('OLLAMA_API_URL', 'http://localhost:11434/api/generate')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'qwen3:latest')

def ask_ollama(prompt: str) -> str:
    payload = {
        'model': OLLAMA_MODEL,
        'prompt': prompt,
        'stream': False
    }
    try:
        response = requests.post(OLLAMA_API_URL, json=payload, timeout=30)
        response.raise_for_status()
        # Ollama pode retornar múltiplos objetos JSON em linhas separadas
        raw = response.text.strip()
        # Tenta pegar o último objeto JSON válido
        import json
        if '\n' in raw:
            lines = [line for line in raw.split('\n') if line.strip()]
            for line in reversed(lines):
                try:
                    data = json.loads(line)
                    return data.get('response', 'Não foi possível obter resposta.')
                except Exception:
                    continue
            return 'Não foi possível obter resposta válida do Ollama.'
        else:
            try:
                data = json.loads(raw)
                return data.get('response', 'Não foi possível obter resposta.')
            except Exception:
                return f'Resposta inválida do Ollama: {raw}'
    except Exception as e:
        return f'Erro ao consultar Ollama: {e}'
