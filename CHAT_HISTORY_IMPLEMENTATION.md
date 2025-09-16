# Chat History Implementation

This document describes the implementation of chat history functionality for the WhatsApp and Telegram bots using the Agno framework.

## Overview

The chatbot now has **conversation memory** that remembers the last **5 interactions** between users and the bot. This allows for more contextual and coherent conversations where the bot can reference previous messages and maintain conversation flow.

## Key Features

✅ **Persistent Storage**: Conversation history is stored in a database and survives bot restarts  
✅ **Session Isolation**: Each user has their own separate conversation history  
✅ **Memory Limit**: Remembers last 5 interactions to balance context and performance  
✅ **Reset Functionality**: Users can clear their conversation history with `/reset` command  
✅ **Cross-Platform**: Works identically on both Telegram and WhatsApp  

## Technical Implementation

### 1. Database Configuration

The system uses SQLite by default for persistent storage:

```bash
# In .env file
DATABASE_URL=sqlite:///./chat_history.db
```

**Supported Database Options:**
- **SQLite**: `sqlite:///./chat_history.db` (recommended for development/small scale)
- **PostgreSQL**: `postgresql://user:password@localhost:5432/chat_history` (recommended for production)

### 2. Agno Agent Configuration

Both Telegram and WhatsApp bots are configured with the following memory parameters:

```python
Agent(
    name="Assistente Agilize NFSe",
    model=OpenRouter(...),
    db=db_storage,                    # Database storage for persistence
    add_history_to_context=True,      # Include conversation history in context
    num_history_runs=5,               # Remember last 5 interactions
    add_datetime_to_context=True,     # Add timestamps for temporal context
    # ... other configurations
)
```

### 3. Session Management

Each user gets a unique session ID:
- **Telegram**: `f"telegram_{user_id}"`
- **WhatsApp**: `f"whatsapp_{from_number}"`

This ensures complete isolation between different users' conversations.

### 4. Reset Functionality

The `/reset` command in Telegram (and equivalent functionality in WhatsApp) clears the conversation history:

```python
async def reset_memory(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reset conversation memory for current user"""
    user_id = str(update.effective_user.id)
    session_id = f"telegram_{user_id}"
    
    # Clear the session history
    if hasattr(self.agent, 'db') and self.agent.db:
        self.agent.db.clear_session(session_id)
```

## Configuration Files

### Environment Variables (.env)

```bash
# Database Configuration for Chat History
DATABASE_URL=sqlite:///./chat_history.db

# OpenRouter Configuration (Required)
OPENROUTER_TOKEN=your_openrouter_api_key_here
OPENROUTER_MODEL=google/gemini-2.5-flash

# Telegram Bot Configuration
ENABLE_TELEGRAM=true
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# WhatsApp Business API Configuration
ENABLE_WHATSAPP=false
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token_here
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id_here
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token_here
WHATSAPP_APP_SECRET=your_app_secret_here
```

### Dependencies (requirements.txt)

```txt
fastapi
uvicorn
python-dotenv
agno
openai
python-telegram-bot
requests
sqlalchemy
```

## File Structure

```
wa-agent-api/
├── app/
│   ├── core/
│   │   └── database.py          # Database configuration module
│   ├── telegram/
│   │   └── agno_bot.py         # Telegram bot with memory enabled
│   └── whatsapp/
│       └── agno_bot.py         # WhatsApp bot with memory enabled
├── test_chat_history.py        # Test script for memory functionality
├── chat_history.db             # SQLite database (auto-created)
├── .env                        # Environment configuration
└── requirements.txt            # Python dependencies
```

## Testing

Run the comprehensive test suite to verify chat history functionality:

```bash
python3 test_chat_history.py
```

The test suite verifies:
- ✅ Database configuration and connectivity
- ✅ Agent configuration with memory parameters
- ✅ Session isolation between users
- ✅ Conversation memory across interactions

## Usage Examples

### Telegram Bot

1. **Start conversation**: `/start`
2. **Normal chat**: "My name is John"
3. **Test memory**: "What's my name?" → Bot responds: "Your name is John"
4. **Reset memory**: `/reset` → Clears conversation history
5. **Test reset**: "What's my name?" → Bot responds: "I don't know your name"

### WhatsApp Bot

1. **Start conversation**: Send any message
2. **Normal chat**: "I work at Agilize"
3. **Test memory**: "Where do I work?" → Bot responds: "You work at Agilize"
4. **Continue conversation**: Bot maintains context across multiple messages

## Memory Behavior

### What is Remembered
- ✅ User messages and bot responses
- ✅ Context from previous interactions
- ✅ Timestamps of conversations
- ✅ Tool calls and their results (if relevant)

### What is NOT Remembered
- ❌ Messages beyond the last 5 interactions
- ❌ Conversations after `/reset` command
- ❌ Cross-session data (each user isolated)
- ❌ System-level information or configurations

### Memory Limits
- **Interaction Limit**: 5 previous interactions (user message + bot response pairs)
- **Time Limit**: No automatic expiration (persists until reset or limit exceeded)
- **Storage Limit**: Depends on database configuration (SQLite: ~280TB theoretical limit)

## Production Considerations

### Database Recommendations
- **Development**: SQLite (`sqlite:///./chat_history.db`)
- **Production**: PostgreSQL with proper backup and scaling
- **High Scale**: Consider database connection pooling and read replicas

### Performance Optimization
- Monitor database size and implement cleanup policies if needed
- Consider increasing `num_history_runs` for more context (trade-off with performance)
- Use database indexing for faster session lookups

### Security
- Ensure database files have proper permissions
- Use environment variables for sensitive configuration
- Consider encryption for sensitive conversation data

### Monitoring
- Monitor database growth and performance
- Track memory usage and response times
- Log conversation reset events for analytics

## Troubleshooting

### Common Issues

1. **"No module named 'agno'"**
   ```bash
   pip3 install agno
   ```

2. **Database connection errors**
   - Check DATABASE_URL format in .env file
   - Ensure database file permissions are correct
   - Verify SQLite/PostgreSQL is properly installed

3. **Memory not working**
   - Verify `add_history_to_context=True` in agent configuration
   - Check that `db` parameter is properly set
   - Ensure session_id is consistent across interactions

4. **Reset command not working**
   - Check that the reset handler is properly registered
   - Verify database connection is working
   - Ensure session_id format matches between reset and normal messages

### Debug Mode

Enable debug mode for troubleshooting:

```python
Agent(
    # ... other parameters
    debug_mode=True,
    debug_level=2  # More verbose logging
)
```

## Future Enhancements

Potential improvements for the chat history system:

- 🔄 **Automatic Cleanup**: Implement automatic cleanup of old conversations
- 📊 **Analytics**: Add conversation analytics and usage metrics  
- 🔍 **Search**: Implement search functionality across conversation history
- 🏷️ **Tagging**: Add conversation tagging and categorization
- 📱 **Export**: Allow users to export their conversation history
- 🔐 **Encryption**: Add end-to-end encryption for sensitive conversations

## Support

For issues or questions about the chat history implementation:

1. Check this documentation first
2. Run the test suite: `python3 test_chat_history.py`
3. Check the logs for error messages
4. Verify environment configuration
5. Open an issue with detailed error information
