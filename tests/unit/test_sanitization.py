"""Unit tests for sanitization utilities."""

import pytest

from app.utils.sanitization import (
    sanitize_dict,
    sanitize_email,
    sanitize_list,
    sanitize_string,
    validate_password_strength,
)


class TestSanitizeString:
    """Test class for sanitize_string function."""
    
    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        input_string = "Hello World"
        result = sanitize_string(input_string)
        
        assert result == "Hello World"
        assert isinstance(result, str)
    
    def test_sanitize_string_with_html(self):
        """Test string sanitization with HTML content."""
        input_string = "<script>alert('xss')</script>Hello"
        result = sanitize_string(input_string)
        
        assert "<script>" not in result
        assert "Hello" in result
    
    def test_sanitize_string_with_null_bytes(self):
        """Test string sanitization removes null bytes."""
        input_string = "Hello\0World"
        result = sanitize_string(input_string)
        
        assert "\0" not in result
        assert result == "HelloWorld"
    
    def test_sanitize_string_non_string_input(self):
        """Test sanitization with non-string input."""
        input_value = 12345
        result = sanitize_string(input_value)
        
        assert result == "12345"
        assert isinstance(result, str)


class TestSanitizeEmail:
    """Test class for sanitize_email function."""
    
    @pytest.mark.parametrize("valid_email", [
        "test@example.com",
        "user.name@domain.co.uk",
        "firstname+lastname@company.org",
    ])
    def test_sanitize_email_valid(self, valid_email):
        """Test email sanitization with valid emails."""
        result = sanitize_email(valid_email)
        
        assert result == valid_email.lower()
        assert "@" in result
    
    @pytest.mark.parametrize("invalid_email", [
        "invalid-email",
        "@domain.com",
        "user@",
        "user space@domain.com",
    ])
    def test_sanitize_email_invalid(self, invalid_email):
        """Test email sanitization with invalid emails."""
        with pytest.raises(ValueError, match="Invalid email format"):
            sanitize_email(invalid_email)
    
    def test_sanitize_email_case_conversion(self):
        """Test that email is converted to lowercase."""
        input_email = "Test.User@EXAMPLE.COM"
        result = sanitize_email(input_email)
        
        assert result == "test.user@example.com"


class TestSanitizeDict:
    """Test class for sanitize_dict function."""
    
    def test_sanitize_dict_basic(self):
        """Test basic dictionary sanitization."""
        input_dict = {
            "name": "John Doe",
            "age": 30,
            "email": "john@example.com"
        }
        result = sanitize_dict(input_dict)
        
        assert isinstance(result, dict)
        assert result["name"] == "John Doe"
        assert result["age"] == 30
        assert result["email"] == "john@example.com"
    
    def test_sanitize_dict_with_html(self):
        """Test dictionary sanitization with HTML content."""
        input_dict = {
            "content": "<script>alert('xss')</script>Hello",
            "safe_content": "Normal text"
        }
        result = sanitize_dict(input_dict)
        
        assert "<script>" not in result["content"]
        assert "Hello" in result["content"]
        assert result["safe_content"] == "Normal text"
    
    def test_sanitize_dict_nested(self):
        """Test sanitization of nested dictionaries."""
        input_dict = {
            "user": {
                "name": "<b>John</b>",
                "details": {
                    "bio": "<script>evil</script>Bio"
                }
            }
        }
        result = sanitize_dict(input_dict)
        
        assert "&lt;b&gt;" in result["user"]["name"]
        assert "<script>" not in result["user"]["details"]["bio"]


class TestSanitizeList:
    """Test class for sanitize_list function."""
    
    def test_sanitize_list_basic(self):
        """Test basic list sanitization."""
        input_list = ["Hello", "World", 123]
        result = sanitize_list(input_list)
        
        assert isinstance(result, list)
        assert result == ["Hello", "World", 123]
    
    def test_sanitize_list_with_html(self):
        """Test list sanitization with HTML content."""
        input_list = ["<script>alert('xss')</script>", "Normal text"]
        result = sanitize_list(input_list)
        
        assert "<script>" not in result[0]
        assert result[0] == ""  # Script content is completely removed
        assert result[1] == "Normal text"


class TestValidatePasswordStrength:
    """Test class for validate_password_strength function."""
    
    def test_valid_password(self):
        """Test with a valid strong password."""
        password = "StrongPass123!"
        result = validate_password_strength(password)
        
        assert result is True
    
    @pytest.mark.parametrize("weak_password,expected_error", [
        ("short", "Password must be at least 8 characters long"),
        ("nouppercase123!", "Password must contain at least one uppercase letter"),
        ("NOLOWERCASE123!", "Password must contain at least one lowercase letter"),
        ("NoNumbers!", "Password must contain at least one number"),
        ("NoSpecialChars123", "Password must contain at least one special character"),
    ])
    def test_weak_passwords(self, weak_password, expected_error):
        """Test various weak password scenarios."""
        with pytest.raises(ValueError, match=expected_error):
            validate_password_strength(weak_password)


