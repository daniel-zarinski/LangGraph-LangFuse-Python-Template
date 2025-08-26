# Testing Guide

This directory contains the test suite for the FastAPI LangGraph Agent application.

## Structure

```
tests/
├── __init__.py                 # Test package initialization
├── conftest.py                # Shared fixtures and configuration
├── README.md                  # This file
├── unit/                      # Unit tests
│   ├── __init__.py
│   ├── test_sanitization.py   # Tests for sanitization utilities
│   └── test_base_model.py     # Tests for base model functionality
└── integration/               # Integration tests
    ├── __init__.py
    └── test_api_endpoints.py  # Tests for API endpoints
```

## Running Tests

### Run All Tests
```bash
# Using pytest directly
pytest

# Using uv
uv run pytest
```

### Run Specific Test Categories
```bash
# Run only unit tests
pytest tests/unit/

# Run only integration tests  
pytest tests/integration/

# Run tests with specific markers
pytest -m unit
pytest -m integration
pytest -m "not slow"
```

### Run Specific Test Files
```bash
# Run sanitization tests
pytest tests/unit/test_sanitization.py

# Run API endpoint tests
pytest tests/integration/test_api_endpoints.py
```

### Run Specific Test Functions/Classes
```bash
# Run specific test function
pytest tests/unit/test_sanitization.py::TestSanitizeString::test_sanitize_string_basic

# Run all tests in a class
pytest tests/unit/test_sanitization.py::TestSanitizeString
```

## Test Configuration

Test configuration is defined in `pyproject.toml`:

```toml
[tool.pytest.ini_options]
markers = ["slow: marks tests as slow (deselect with '-m \"not slow\"')"]
python_files = ["test_*.py", "*_test.py", "tests.py"]
```

## Common Testing Patterns

### 1. Basic Test Structure (AAA Pattern)
```python
def test_function_name():
    # Arrange - Set up test data
    input_data = "test input"
    
    # Act - Call the function being tested
    result = function_to_test(input_data)
    
    # Assert - Check the results
    assert result == expected_output
```

### 2. Using Fixtures
```python
def test_with_fixture(sample_user_data):
    # Fixture provides data automatically
    assert sample_user_data["email"] == "test@example.com"
```

### 3. Parametrized Tests
```python
@pytest.mark.parametrize("input,expected", [
    ("hello", "hello"),
    ("HELLO", "hello"),
])
def test_lowercase(input, expected):
    assert input.lower() == expected
```

### 4. Exception Testing
```python
def test_function_raises_exception():
    with pytest.raises(ValueError, match="Expected error message"):
        function_that_should_raise()
```

### 5. Mocking External Dependencies
```python
@patch('module.external_service')
def test_with_mock(mock_service):
    mock_service.return_value = "mocked response"
    result = function_using_service()
    assert result == "mocked response"
```

## Available Fixtures
- `test_environment`: Complete environment variable setup for testing (session-scoped)
- `test_client`: FastAPI test client with proper environment setup
- `sample_user_data`: User registration/login data
- `sample_chat_message`: Chat message data for testing chat endpoints
- `mock_llm_response`: Mocked LLM response for testing without external APIs
- `auth_headers`: Authentication headers for testing protected endpoints

## Test Markers

Use markers to categorize and selectively run tests:

- `@pytest.mark.unit`: Unit tests
- `@pytest.mark.integration`: Integration tests
- `@pytest.mark.slow`: Slow-running tests
- `@pytest.mark.e2e`: End-to-end tests

## Best Practices

1. **Follow AAA Pattern**: Arrange, Act, Assert
2. **Use descriptive test names**: `test_function_behavior_expected_result`
3. **One assertion per test**: Keep tests focused
4. **Use fixtures for setup**: Avoid repetitive setup code
5. **Mock external dependencies**: Keep tests isolated and fast
6. **Use parametrize for multiple scenarios**: Test various inputs efficiently
7. **Test edge cases**: Include boundary conditions and error scenarios
8. **Keep tests independent**: Tests should not depend on each other

## Coverage

To run tests with coverage reporting:

```bash
# Install coverage if not already installed
uv add --group dev pytest-cov

# Run tests with coverage
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

## Debugging Tests

To debug failing tests:

```bash
# Run with verbose output
pytest -v

# Stop on first failure
pytest -x

# Enter debugger on failure
pytest --pdb

# Run specific test with print statements
pytest -s tests/unit/test_sanitization.py::test_specific_function
```
