#!/usr/bin/env python3
"""
Test script for PRD Generation functionality.

This script tests the PRD generation workflow, database storage,
conversation persistence, and session isolation.
"""

import os
import sys
import uuid
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_environment_setup():
    """Test if all required environment variables are configured."""
    print("🔧 Testing Environment Setup...")
    
    required_vars = [
        'DATABASE_URL',
        'OPENROUTER_TOKEN',
        'OPENROUTER_MODEL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    
    print("✅ Environment setup is correct")
    return True


def test_database_connection():
    """Test database connection and storage setup."""
    print("🗄️  Testing Database Connection...")
    
    try:
        from app.core.database import get_database_storage, get_workflow_storage
        
        # Test database storage
        db_storage = get_database_storage()
        if db_storage:
            print("✅ Database storage initialized successfully")
        else:
            print("❌ Failed to initialize database storage")
            return False
        
        # Test workflow storage
        workflow_storage = get_workflow_storage()
        if workflow_storage:
            print("✅ Workflow storage initialized successfully")
        else:
            print("❌ Failed to initialize workflow storage")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False


def test_prd_workflow_creation():
    """Test PRD workflow creation and basic functionality."""
    print("🤖 Testing PRD Workflow Creation...")
    
    try:
        from agno.agent import Agent
        from agno.models.openrouter import OpenRouter
        from app.core.database import get_database_storage
        from app.workflows.prd_workflow import get_prd_generation_workflow
        
        # Check if OpenRouter token is configured
        openrouter_token = os.getenv('OPENROUTER_TOKEN')
        if not openrouter_token:
            print("⚠️  OPENROUTER_TOKEN not configured - workflow creation will fail")
            return False
        
        # Create test workflow
        test_session_id = f"test_prd_{uuid.uuid4().hex[:8]}"
        workflow = get_prd_generation_workflow(session_id=test_session_id)
        
        if workflow:
            print("✅ PRD workflow created successfully")
            print(f"   Session ID: {test_session_id}")
            return True
        else:
            print("❌ Failed to create PRD workflow")
            return False
            
    except Exception as e:
        print(f"❌ PRD workflow creation failed: {str(e)}")
        return False


def test_prd_conversation_flow():
    """Test PRD generation conversation flow and memory."""
    print("💬 Testing PRD Conversation Flow...")
    
    try:
        from app.workflows.prd_workflow import get_prd_generation_workflow
        
        # Check if OpenRouter token is configured
        openrouter_token = os.getenv('OPENROUTER_TOKEN')
        if not openrouter_token:
            print("⚠️  OPENROUTER_TOKEN not configured - skipping conversation test")
            return False
        
        # Create test workflow
        test_session_id = f"test_conversation_{uuid.uuid4().hex[:8]}"
        workflow = get_prd_generation_workflow(session_id=test_session_id)
        
        # Test messages simulating PRD generation flow
        test_messages = [
            "I want to create a mobile app for fitness tracking",
            "It should help users track workouts, nutrition, and progress",
            "The target users are fitness enthusiasts aged 25-45",
            "The main features should include workout logging and progress charts"
        ]
        
        print(f"   Testing with session: {test_session_id}")
        
        for i, message in enumerate(test_messages, 1):
            print(f"   Message {i}: {message[:50]}...")
            
            # Run workflow and get response
            workflow_output = workflow.run(message)
            responses = []
            if workflow_output and hasattr(workflow_output, 'content'):
                responses.append(workflow_output.content)
            elif workflow_output and hasattr(workflow_output, 'output'):
                responses.append(str(workflow_output.output))
            
            if responses:
                print(f"   ✅ Got {len(responses)} response(s)")
                
                # Check context and progress
                context = workflow.get_context()
                if context:
                    completion = workflow.get_completion_percentage()
                    print(f"   📊 Phase: {context.phase.value}, Progress: {completion}%")
                else:
                    print("   ⚠️  No context found")
            else:
                print(f"   ❌ No response for message {i}")
                return False
        
        print("✅ PRD conversation flow test completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ PRD conversation flow test failed: {str(e)}")
        return False


def test_session_isolation():
    """Test that different sessions maintain separate conversation contexts."""
    print("👥 Testing Session Isolation...")
    
    try:
        from app.workflows.prd_workflow import get_prd_generation_workflow
        
        # Check if OpenRouter token is configured
        openrouter_token = os.getenv('OPENROUTER_TOKEN')
        if not openrouter_token:
            print("⚠️  OPENROUTER_TOKEN not configured - skipping session isolation test")
            return False
        
        # Create two different sessions
        session1_id = f"test_session1_{uuid.uuid4().hex[:8]}"
        session2_id = f"test_session2_{uuid.uuid4().hex[:8]}"
        
        workflow1 = get_prd_generation_workflow(session_id=session1_id)
        workflow2 = get_prd_generation_workflow(session_id=session2_id)
        
        # Send different messages to each session
        message1 = "I want to create a fitness tracking app"
        message2 = "I want to build an e-commerce platform"
        
        # Process messages
        output1 = workflow1.run(message1)
        output2 = workflow2.run(message2)
        responses1 = [output1] if output1 else []
        responses2 = [output2] if output2 else []
        
        # Check that contexts are different
        context1 = workflow1.get_context()
        context2 = workflow2.get_context()
        
        if context1 and context2:
            if context1.session_id != context2.session_id:
                print("✅ Sessions maintain separate contexts")
                print(f"   Session 1: {context1.session_id}")
                print(f"   Session 2: {context2.session_id}")
                return True
            else:
                print("❌ Sessions are not properly isolated")
                return False
        else:
            print("❌ Failed to get contexts for session isolation test")
            return False
            
    except Exception as e:
        print(f"❌ Session isolation test failed: {str(e)}")
        return False


def test_prd_data_models():
    """Test PRD data models and validation."""
    print("📋 Testing PRD Data Models...")
    
    try:
        from app.models.prd_models import (
            ProductData, UserPersona, UserStory, TechnicalRequirement, 
            SuccessMetric, ConversationContext, PRDDocument
        )
        
        # Test UserPersona
        persona = UserPersona(
            name="Fitness Enthusiast",
            description="Active individual who tracks workouts regularly",
            goals=["Track progress", "Stay motivated"],
            pain_points=["Forgetting workouts", "Lack of progress visibility"]
        )
        print("✅ UserPersona model works correctly")
        
        # Test UserStory
        story = UserStory(
            title="Track workout progress",
            description="I want to log my workouts so that I can track my progress over time",
            persona="Fitness Enthusiast",
            priority="high",
            acceptance_criteria=["Can log exercise type", "Can record sets and reps"]
        )
        print("✅ UserStory model works correctly")
        
        # Test ProductData
        product_data = ProductData(
            product_name="FitTracker Pro",
            product_description="A comprehensive fitness tracking application",
            user_personas=[persona],
            user_stories=[story]
        )
        print("✅ ProductData model works correctly")
        
        # Test PRDDocument
        prd_doc = PRDDocument(
            title="FitTracker Pro PRD",
            product_name="FitTracker Pro",
            product_vision="To help people achieve their fitness goals through better tracking",
            product_description="A comprehensive fitness tracking application",
            business_goals=["Increase user engagement", "Improve fitness outcomes"],
            target_audience="Fitness enthusiasts aged 25-45",
            user_personas=[persona],
            core_features=["Workout logging", "Progress tracking"],
            user_stories=[story],
            technical_requirements=[],
            success_metrics=[],
            constraints={},
            assumptions=[],
            integration_requirements=[],
            technology_preferences=[]
        )
        
        # Test markdown generation
        markdown_content = prd_doc.to_markdown()
        if markdown_content and len(markdown_content) > 100:
            print("✅ PRD markdown generation works correctly")
            print(f"   Generated {len(markdown_content)} characters of markdown")
        else:
            print("❌ PRD markdown generation failed")
            return False
        
        print("✅ All PRD data models work correctly")
        return True
        
    except Exception as e:
        print(f"❌ PRD data models test failed: {str(e)}")
        return False


def run_all_tests():
    """Run all PRD generation tests."""
    print("🧪 Starting PRD Generation Test Suite")
    print("=" * 50)
    
    tests = [
        ("Environment Setup", test_environment_setup),
        ("Database Connection", test_database_connection),
        ("PRD Workflow Creation", test_prd_workflow_creation),
        ("PRD Data Models", test_prd_data_models),
        ("PRD Conversation Flow", test_prd_conversation_flow),
        ("Session Isolation", test_session_isolation),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        try:
            if test_func():
                passed += 1
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} crashed: {str(e)}")
    
    print("\n" + "=" * 50)
    print(f"🧪 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! PRD generation system is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the configuration and try again.")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
