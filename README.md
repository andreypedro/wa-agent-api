# WA Agent API

This project is an API for WhatsApp and Telegram agents, integrating AI models via OpenRouter and NFSe functions.

## 🆕 New Features

- **💬 Chat History**: Bots now remember the last 5 interactions for contextual conversations
- **🗄️ Persistent Storage**: Conversation history survives bot restarts using SQLite/PostgreSQL
- **🔄 Reset Command**: Users can clear their conversation history with `/reset` (Telegram)
- **👥 Session Isolation**: Each user has their own separate conversation memory

## Requirements

- Python 3.9+
- Install dependencies: `pip install -r requirements.txt`
- Set environment variables (you can use a `.env` file):
  - `OPENROUTER_TOKEN` (OpenRouter token)
  - `OPENROUTER_MODEL` (optional, model to use)
  - `DATABASE_URL` (optional, for persistent chat history: `sqlite:///./chat_history.db`)

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

- `main.py`: API entry point with FastAPI
- `app/workflows/lead_workflow.py`: Lead conversion state machine
- `app/services/audio_transcription.py`: Speech recognition service
- `app/telegram/agno_bot.py`: Telegram bot with voice support
- `app/whatsapp/agno_bot.py`: WhatsApp bot integration
- `app/models/lead_models.py`: Data models and conversation context
- `app/core/database.py`: Database configuration and storage
- `monitor_conversations.py`: Real-time conversation data monitoring

## 🐳 Docker Setup (Recommended)

The easiest way to run the application with chat history:

```bash
# Quick start
./run-docker.sh start

# View logs
./run-docker.sh logs

# Test chat history
./run-docker.sh test

# Stop application
./run-docker.sh stop
```

See [Docker Setup Guide](DOCKER_SETUP.md) for detailed instructions.

## 🧪 Testing Chat History

Test the chat history functionality:

```bash
# Local testing
python3 test_chat_history.py

# Docker testing
./run-docker.sh test
```

This will verify:
- Database configuration
- Agent memory settings
- Conversation persistence
- Session isolation

## 📚 Documentation

- **[Chat History Implementation](CHAT_HISTORY_IMPLEMENTATION.md)**: Detailed documentation about the conversation memory system
- **[Environment Configuration](.env.example)**: Example environment variables

## Notes

- The project uses Agno framework for AI agent integration.
- NFSe functions are automatically called when the model returns JSON with `function_call`.
- Chat history remembers the last 5 interactions per user for contextual conversations.

## Questions

Open an issue or contact the maintainer.
