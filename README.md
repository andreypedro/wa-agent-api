# WA Agent API

Este projeto é uma API para agentes de WhatsApp e Telegram, integrando modelos de IA via OpenRouter e funções de NFSe.

## Requisitos

- Python 3.9+
- Instalar dependências: `pip install -r requirements.txt`
- Configurar variáveis de ambiente (pode usar um arquivo `.env`):
  - `OPENROUTER_TOKEN` (token da OpenRouter)
  - `OPENROUTER_MODEL` (opcional, modelo a ser usado)

## Como rodar a API

1. Inicie o servidor FastAPI (usando Uvicorn):

   ```bash
   python3 -m uvicorn main:app --reload
   ```

   O servidor estará disponível em `http://localhost:8000`.

2. Para rodar o bot do Telegram:
   - Configure o token do bot no arquivo de configuração.
   - Execute o bot (exemplo):
     ```bash
     python3 app/telegram/bot.py
     ```

## Estrutura do projeto

- `main.py`: Ponto de entrada da API.
- `app/agents/nfse_agent.py`: Funções de NFSe.
- `app/core/openrouter_client.py`: Cliente para integração com OpenRouter.
- `app/telegram/bot.py`: Bot do Telegram.
- `app/whatsapp/`: (estrutura para integração WhatsApp)

## Observações

- O projeto utiliza LangChain para integração com modelos de IA.
- As funções de NFSe são chamadas automaticamente quando o modelo retorna JSON com `function_call`.

## Dúvidas

Abra uma issue ou entre em contato com o mantenedor.
