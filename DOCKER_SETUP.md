# Docker Setup Guide

This guide explains how to run the WA Agent API with chat history functionality using Docker.

## 🚀 Quick Start

### 1. Prerequisites

- Docker and Docker Compose installed
- `.env` file configured with your API keys

### 2. Easy Setup

```bash
# Make the script executable (first time only)
chmod +x run-docker.sh

# Start the application
./run-docker.sh start
```

That's it! The application will be available at `http://localhost:8000`

## 📋 Available Commands

```bash
./run-docker.sh start    # Start in development mode (default)
./run-docker.sh prod     # Start in production mode  
./run-docker.sh stop     # Stop the application
./run-docker.sh restart  # Restart the application
./run-docker.sh logs     # Show application logs
./run-docker.sh status   # Show application status
./run-docker.sh test     # Test chat history functionality
./run-docker.sh clean    # Stop and remove all containers
./run-docker.sh help     # Show help message
```

## 🔧 Configuration

### Environment Variables (.env)

The script will check for required environment variables:

```bash
# Required
OPENROUTER_TOKEN=your_openrouter_api_key_here
OPENROUTER_MODEL=google/gemini-2.5-flash

# Telegram (if enabled)
ENABLE_TELEGRAM=true
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# WhatsApp (if enabled)  
ENABLE_WHATSAPP=false
WHATSAPP_ACCESS_TOKEN=your_whatsapp_access_token_here
WHATSAPP_PHONE_NUMBER_ID=your_phone_number_id_here
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_webhook_verify_token_here
WHATSAPP_APP_SECRET=your_app_secret_here

# Database (automatically configured for Docker)
DATABASE_URL=sqlite:///./data/chat_history.db
```

### Database Persistence

The Docker setup automatically handles database persistence:

- **Development**: Database stored in `./data/chat_history.db`
- **Production**: Same location, but with production optimizations
- **Backup**: Simply backup the `./data/` directory

## 🏗️ Docker Architecture

### Development Mode (`docker-compose.yml`)

```yaml
services:
  wa-agent-api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./app:/app/app          # Hot reload for development
      - ./data:/app/data        # Database persistence
    environment:
      - DATABASE_URL=sqlite:///./data/chat_history.db
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
```

### Production Mode (`docker-compose.prod.yml`)

```yaml
services:
  wa-agent-api:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data        # Only database persistence
    environment:
      - DATABASE_URL=sqlite:///./data/chat_history.db
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

## 🧪 Testing

### Automated Testing

```bash
# Test chat history functionality
./run-docker.sh test
```

This will:
1. Wait for the container to start
2. Run the chat history test suite inside the container
3. Verify database configuration and memory functionality

### Manual Testing

```bash
# Check application status
./run-docker.sh status

# View logs
./run-docker.sh logs

# Test API endpoints
curl http://localhost:8000/health
curl http://localhost:8000/
```

### Chat History Testing

1. **Start the application**: `./run-docker.sh start`
2. **Test Telegram bot** (if configured):
   - Send `/start` to your bot
   - Send "My name is John"
   - Send "What's my name?" → Should respond with "John"
   - Send `/reset` to clear history
   - Send "What's my name?" → Should not remember

## 📁 File Structure

```
wa-agent-api/
├── docker-compose.yml          # Development Docker setup
├── docker-compose.prod.yml     # Production Docker setup
├── Dockerfile                  # Container definition
├── run-docker.sh              # Easy Docker management script
├── data/                      # Database persistence directory
│   └── chat_history.db        # SQLite database (auto-created)
├── app/                       # Application source code
├── .env                       # Environment configuration
└── requirements.txt           # Python dependencies
```

## 🔍 Monitoring & Logs

### View Logs

```bash
# Follow logs in real-time
./run-docker.sh logs

# Or use Docker Compose directly
docker-compose logs -f wa-agent-api
```

### Health Monitoring

The application includes health checks:

```bash
# Check health status
curl http://localhost:8000/health

# Response example:
{
  "status": "healthy",
  "framework": "agno",
  "channels": {
    "telegram_enabled": true,
    "whatsapp_enabled": false
  }
}
```

### Container Status

```bash
# Check container status
./run-docker.sh status

# Or use Docker directly
docker-compose ps
```

## 🚨 Troubleshooting

### Common Issues

1. **Port 8000 already in use**
   ```bash
   # Stop any existing containers
   ./run-docker.sh clean
   
   # Or change port in docker-compose.yml
   ports:
     - "8001:8000"  # Use port 8001 instead
   ```

2. **Database permission issues**
   ```bash
   # Fix data directory permissions
   sudo chown -R $USER:$USER ./data
   chmod 755 ./data
   ```

3. **Container won't start**
   ```bash
   # Check logs for errors
   ./run-docker.sh logs
   
   # Rebuild container
   docker-compose build --no-cache
   ./run-docker.sh start
   ```

4. **Chat history not working**
   ```bash
   # Test chat history functionality
   ./run-docker.sh test
   
   # Check database file
   ls -la ./data/chat_history.db
   ```

### Debug Mode

Enable debug mode by adding to `.env`:

```bash
AGNO_DEBUG=true
```

Then restart:

```bash
./run-docker.sh restart
```

## 🔄 Updates & Maintenance

### Updating the Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
./run-docker.sh clean
./run-docker.sh start
```

### Database Backup

```bash
# Backup database
cp ./data/chat_history.db ./data/chat_history.db.backup

# Or backup entire data directory
tar -czf backup-$(date +%Y%m%d).tar.gz ./data/
```

### Container Maintenance

```bash
# Clean up unused Docker resources
docker system prune

# Remove old images
docker image prune

# View disk usage
docker system df
```

## 🌐 Production Deployment

### Using Production Mode

```bash
# Start in production mode
./run-docker.sh prod
```

### Production Considerations

1. **Environment Variables**: Use secure values, not defaults
2. **Database**: Consider PostgreSQL for high scale
3. **Reverse Proxy**: Use nginx or similar for SSL/load balancing
4. **Monitoring**: Implement proper logging and monitoring
5. **Backups**: Set up automated database backups

### PostgreSQL Setup (Optional)

Uncomment the PostgreSQL service in `docker-compose.prod.yml` and update your `.env`:

```bash
DATABASE_URL=postgresql://agno_user:your_secure_password@postgres:5432/chat_history
```

## 📞 Support

If you encounter issues:

1. Check the logs: `./run-docker.sh logs`
2. Test functionality: `./run-docker.sh test`
3. Check status: `./run-docker.sh status`
4. Review this documentation
5. Check the main [Chat History Implementation](CHAT_HISTORY_IMPLEMENTATION.md) guide

## 🎯 Next Steps

After successful Docker deployment:

1. Configure your bot tokens in `.env`
2. Test chat history functionality
3. Set up webhooks for WhatsApp (if using)
4. Monitor logs and performance
5. Set up backups for production use

The Docker setup provides a robust, scalable foundation for running your chatbot with persistent conversation memory! 🚀
