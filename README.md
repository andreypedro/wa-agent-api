# WA Agent API

This project is an API for WhatsApp and Telegram agents, integrating AI models via OpenRouter and NFSe functions.

## Requirements

- Python 3.9+
- Install dependencies: `pip install -r requirements.txt`
- Set environment variables (you can use a `.env` file):
  - `OPENROUTER_TOKEN` (OpenRouter token)
  - `OPENROUTER_MODEL` (optional, model to use)

## How to run the API

1. Start the FastAPI server (using Uvicorn):

   ```bash
   python3 -m uvicorn main:app --reload
   ```

   The server will be available at `http://localhost:8000`.

2. To run the Telegram bot:
   - Set the bot token in the configuration file.
   - Run the bot (example):
     ```bash
     python3 app/telegram/bot.py
     ```

## Project structure

- `main.py`: API entry point.
- `app/agents/nfse_agent.py`: NFSe functions.
- `app/core/openrouter_client.py`: OpenRouter integration client.
- `app/telegram/bot.py`: Telegram bot.
- `app/whatsapp/`: (structure for WhatsApp integration)

## Notes

- The project uses LangChain for AI model integration.
- NFSe functions are automatically called when the model returns JSON with `function_call`.

## Questions

Open an issue or contact the maintainer.
