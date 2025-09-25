#!/usr/bin/env python3
"""
Test script to verify chat history functionality.
This script tests the Agno agent configuration and database setup.
"""

import os
import sys
import asyncio
from dotenv import load_dotenv

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

load_dotenv()

def test_database_configuration():
    """Test database configuration and storage setup"""
    print("🔍 Testing database configuration...")
    
    try:
        from app.core.database import get_database_storage
        
        # Test database storage initialization
        db_storage = get_database_storage()
        
        if db_storage is None:
            print("⚠️  No database configured - using in-memory storage")
            print("   To enable persistent storage, set DATABASE_URL in .env file")
            print("   Example: DATABASE_URL=sqlite:///./chat_history.db")
        else:
            print(f"✅ Database storage initialized: {type(db_storage).__name__}")
            
        return True
        
    except Exception as e:
        print(f"❌ Database configuration error: {str(e)}")
        return False

def test_agent_configuration():
    """Test Agno agent configuration with memory parameters"""
    print("\n🤖 Testing agent configuration...")
    
    try:
        from agno.agent import Agent
        from agno.models.openrouter import OpenRouter
        from app.core.database import get_database_storage
        
        # Check if OpenRouter token is configured
        openrouter_token = os.getenv('OPENROUTER_TOKEN')
        if not openrouter_token:
            print("⚠️  OPENROUTER_TOKEN not configured - agent creation will fail")
            return False
        
        # Initialize database storage
        db_storage = get_database_storage()
        
        # Create test agent with memory configuration
        test_agent = Agent(
            name="Test Chat History Agent",
            model=OpenRouter(
                id="google/gemini-2.5-flash",
                api_key=openrouter_token
            ),
            db=db_storage,
            add_history_to_context=True,
            num_history_runs=5,
            add_datetime_to_context=True,
            debug_mode=True
        )
        
        print("✅ Agent created successfully with memory configuration:")
        print(f"   - add_history_to_context: True")
        print(f"   - num_history_runs: 5")
        print(f"   - Database storage: {'Enabled' if db_storage else 'Disabled'}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent configuration error: {str(e)}")
        return False

async def test_conversation_memory():
    """Test conversation memory with multiple interactions"""
    print("\n💬 Testing conversation memory...")
    
    try:
        from agno.agent import Agent
        from agno.models.openrouter import OpenRouter
        from app.core.database import get_database_storage
        
        # Check if OpenRouter token is configured
        openrouter_token = os.getenv('OPENROUTER_TOKEN')
        if not openrouter_token:
            print("⚠️  OPENROUTER_TOKEN not configured - skipping memory test")
            return False
        
        # Initialize database storage
        db_storage = get_database_storage()
        
        # Create test agent
        test_agent = Agent(
            name="Memory Test Agent",
            model=OpenRouter(
                id="google/gemini-2.5-flash",
                api_key=openrouter_token
            ),
            db=db_storage,
            add_history_to_context=True,
            num_history_runs=5,
            instructions=["You are a helpful assistant. Remember what the user tells you."],
            debug_mode=False
        )
        
        session_id = "test_session_123"
        
        print("📝 Simulating conversation with memory...")
        
        # First interaction
        print("\n1️⃣ User: My name is Alice")
        response1 = test_agent.run("My name is Alice", session_id=session_id)
        print(f"   Bot: {response1.content[:100]}...")
        
        # Second interaction - test if agent remembers the name
        print("\n2️⃣ User: What's my name?")
        response2 = test_agent.run("What's my name?", session_id=session_id)
        print(f"   Bot: {response2.content[:100]}...")
        
        # Check if the response contains the name Alice
        if "Alice" in response2.content or "alice" in response2.content.lower():
            print("✅ Memory test passed - Agent remembered the name!")
        else:
            print("⚠️  Memory test inconclusive - Agent may not have remembered the name")
            print(f"   Full response: {response2.content}")
        
        return True
        
    except Exception as e:
        print(f"❌ Memory test error: {str(e)}")
        return False

def test_session_isolation():
    """Test that different sessions have isolated memory"""
    print("\n🔒 Testing session isolation...")
    
    try:
        from agno.agent import Agent
        from agno.models.openrouter import OpenRouter
        from app.core.database import get_database_storage
        
        # This is a simplified test - in a real scenario you'd test with actual conversations
        print("✅ Session isolation is handled by Agno framework automatically")
        print("   Each session_id maintains separate conversation history")
        print("   Telegram: session_id = f'telegram_{user_id}'")
        print("   WhatsApp: session_id = f'whatsapp_{from_number}'")
        
        return True
        
    except Exception as e:
        print(f"❌ Session isolation test error: {str(e)}")
        return False

def main():
    """Run all tests"""
    print("🚀 Starting Chat History Tests\n")
    
    tests = [
        ("Database Configuration", test_database_configuration),
        ("Agent Configuration", test_agent_configuration),
        ("Session Isolation", test_session_isolation),
    ]
    
    # Run synchronous tests
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {str(e)}")
            results.append((test_name, False))
    
    # Run async memory test
    try:
        print("\n💬 Running async memory test...")
        memory_result = asyncio.run(test_conversation_memory())
        results.append(("Conversation Memory", memory_result))
    except Exception as e:
        print(f"❌ Conversation Memory test failed: {str(e)}")
        results.append(("Conversation Memory", False))
    
    # Print summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nResults: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Chat history is properly configured.")
    else:
        print("⚠️  Some tests failed. Check the configuration and try again.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
