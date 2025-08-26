"""Pytest configuration and shared fixtures.

This file contains pytest configuration and fixtures that are available
to all test files in the test suite for your FastAPI LangGraph Agent application.
"""

import os
from typing import Any, Dict
from unittest.mock import Mock

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(scope="session")
def test_environment():
    """Set up test environment variables for the entire test session."""
    # Store original environment values to restore later
    original_env = {}
    
    # Test environment variables for your FastAPI LangGraph Agent
    test_env_vars = {
        "ENVIRONMENT": "test",
        "PROJECT_NAME": "Test FastAPI LangGraph Agent",
        "VERSION": "test-1.0.0",
        "DEBUG": "true",
        "LOG_LEVEL": "DEBUG",
        
        # Database
        "POSTGRES_URL": "postgresql://test:test@localhost:5432/test_db",
        
        # LLM Configuration  
        "LLM_API_KEY": "test-openai-key-12345",
        "GOOGLE_API_KEY": "test-google-key-12345",
        "LLM_MODEL": "gpt-4o-mini",
        "DEFAULT_LLM_TEMPERATURE": "0.1",
        "MAX_TOKENS": "1000",
        
        # JWT
        "JWT_SECRET_KEY": "test-secret-key-for-jwt-signing",
        "JWT_ALGORITHM": "HS256",
        "JWT_ACCESS_TOKEN_EXPIRE_DAYS": "1",
        
        # Langfuse (mocked)
        "LANGFUSE_PUBLIC_KEY": "test-public-key",
        "LANGFUSE_SECRET_KEY": "test-secret-key",
        "LANGFUSE_HOST": "https://test.langfuse.com",
        
        # Rate limiting (relaxed for testing)
        "RATE_LIMIT_DEFAULT": "1000 per hour",
    }
    
    # Set test environment variables
    for key, value in test_env_vars.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
    
    yield test_env_vars
    
    # Restore original environment
    for key, original_value in original_env.items():
        if original_value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = original_value


@pytest.fixture
def test_client(test_environment):
    """Create a test client for the FastAPI app."""
    # Import here to ensure test environment is set up first
    from app.main import app
    
    return TestClient(app)


@pytest.fixture
def sample_user_data() -> Dict[str, Any]:
    """Sample user data for testing authentication endpoints."""
    return {
        "email": "testuser@example.com",
        "password": "TestPassword123!",
        "username": "testuser"
    }


@pytest.fixture
def sample_chat_message() -> Dict[str, Any]:
    """Sample chat message data for testing chat endpoints."""
    return {
        "message": "Hello, I need help with my FastAPI application",
        "thread_id": "test-thread-12345"
    }


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing without hitting real APIs."""
    return {
        "content": "This is a mocked response from the LLM for testing purposes.",
        "usage": {"prompt_tokens": 10, "completion_tokens": 15, "total_tokens": 25},
        "model": "gpt-4o-mini"
    }


@pytest.fixture
def auth_headers(sample_user_data) -> Dict[str, str]:
    """Generate authentication headers for testing protected endpoints."""
    # In a real test, you might create an actual JWT token
    # For now, we'll use a mock token
    mock_token = "test-jwt-token-12345"
    return {"Authorization": f"Bearer {mock_token}"}


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers for this project."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "llm: mark test as requiring LLM integration"
    )
    config.addinivalue_line(
        "markers", "database: mark test as requiring database"
    )
    config.addinivalue_line(
        "markers", "auth: mark test as requiring authentication"
    )