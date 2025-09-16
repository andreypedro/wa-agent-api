#!/bin/bash

# WA Agent API Docker Runner
# This script helps you run the chatbot with chat history in Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if .env file exists and has required variables
check_env() {
    if [ ! -f .env ]; then
        print_error ".env file not found!"
        print_status "Creating .env file from template..."
        cp .env.example .env
        print_warning "Please edit .env file with your actual API keys and tokens"
        print_status "Required variables:"
        echo "  - OPENROUTER_TOKEN (required)"
        echo "  - TELEGRAM_BOT_TOKEN (if using Telegram)"
        echo "  - WHATSAPP_* variables (if using WhatsApp)"
        exit 1
    fi
    
    # Check for required OPENROUTER_TOKEN
    if ! grep -q "OPENROUTER_TOKEN=" .env || grep -q "OPENROUTER_TOKEN=your_openrouter_api_key_here" .env; then
        print_error "OPENROUTER_TOKEN not configured in .env file"
        print_status "Please set your OpenRouter API key in .env file"
        exit 1
    fi
    
    print_success ".env file configured"
}

# Function to create data directory
setup_data_dir() {
    if [ ! -d "data" ]; then
        print_status "Creating data directory for database persistence..."
        mkdir -p data
        print_success "Data directory created"
    else
        print_status "Data directory already exists"
    fi
}

# Function to test chat history functionality
test_chat_history() {
    print_status "Testing chat history functionality..."
    
    # Wait for container to be ready
    print_status "Waiting for container to start..."
    sleep 10
    
    # Check if container is healthy
    if docker-compose ps | grep -q "healthy"; then
        print_success "Container is healthy"
        
        # Run chat history test inside container
        print_status "Running chat history tests..."
        docker-compose exec wa-agent-api python3 test_chat_history.py
        
        if [ $? -eq 0 ]; then
            print_success "Chat history tests passed!"
        else
            print_warning "Chat history tests had issues, but container is running"
        fi
    else
        print_warning "Container health check not available, but container should be running"
    fi
}

# Function to show logs
show_logs() {
    print_status "Showing container logs (press Ctrl+C to exit)..."
    docker-compose logs -f wa-agent-api
}

# Function to show status
show_status() {
    print_status "Container status:"
    docker-compose ps
    
    print_status "Health check:"
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "Health endpoint not responding"
    
    print_status "Database file:"
    if [ -f "data/chat_history.db" ]; then
        ls -lh data/chat_history.db
        print_success "Database file exists"
    else
        print_warning "Database file not found (will be created on first use)"
    fi
}

# Function to clean up
cleanup() {
    print_status "Stopping and removing containers..."
    docker-compose down
    print_success "Cleanup complete"
}

# Function to show help
show_help() {
    echo "WA Agent API Docker Runner"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  start       Start the application in development mode (default)"
    echo "  prod        Start the application in production mode"
    echo "  stop        Stop the application"
    echo "  restart     Restart the application"
    echo "  logs        Show application logs"
    echo "  status      Show application status"
    echo "  test        Test chat history functionality"
    echo "  clean       Stop and remove all containers"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 start    # Start in development mode"
    echo "  $0 prod     # Start in production mode"
    echo "  $0 logs     # View logs"
    echo "  $0 test     # Test chat history"
}

# Main script logic
case "${1:-start}" in
    "start")
        print_status "Starting WA Agent API in development mode..."
        check_env
        setup_data_dir
        
        print_status "Building and starting containers..."
        docker-compose up -d --build
        
        print_success "Application started!"
        print_status "API available at: http://localhost:8000"
        print_status "Health check: http://localhost:8000/health"
        print_status ""
        print_status "Use '$0 logs' to view logs"
        print_status "Use '$0 test' to test chat history"
        print_status "Use '$0 stop' to stop the application"
        ;;
        
    "prod")
        print_status "Starting WA Agent API in production mode..."
        check_env
        setup_data_dir
        
        print_status "Building and starting containers (production)..."
        docker-compose -f docker-compose.prod.yml up -d --build
        
        print_success "Application started in production mode!"
        print_status "API available at: http://localhost:8000"
        ;;
        
    "stop")
        print_status "Stopping WA Agent API..."
        docker-compose down
        print_success "Application stopped"
        ;;
        
    "restart")
        print_status "Restarting WA Agent API..."
        docker-compose restart
        print_success "Application restarted"
        ;;
        
    "logs")
        show_logs
        ;;
        
    "status")
        show_status
        ;;
        
    "test")
        test_chat_history
        ;;
        
    "clean")
        cleanup
        ;;
        
    "help"|"-h"|"--help")
        show_help
        ;;
        
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
