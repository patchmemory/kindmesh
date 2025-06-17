import pytest

# Import the module to test
from kindmesh.password_policy import validate_password, get_password_requirements

class TestPasswordPolicy:
    """Unit tests for the password policy module"""

    def test_valid_password(self):
        """Test that a valid password passes validation"""
        valid_password = "Password123!"
        is_valid, errors = validate_password(valid_password)
        assert is_valid
        assert len(errors) == 0

    def test_short_password(self):
        """Test that a short password fails validation"""
        short_password = "Pass1!"
        is_valid, errors = validate_password(short_password)
        assert not is_valid
        assert "Password must be at least 8 characters long" in errors

    def test_no_lowercase(self):
        """Test that a password without lowercase letters fails validation"""
        no_lowercase = "PASSWORD123!"
        is_valid, errors = validate_password(no_lowercase)
        assert not is_valid
        assert "Password must contain at least one lowercase letter" in errors

    def test_no_uppercase(self):
        """Test that a password without uppercase letters fails validation"""
        no_uppercase = "password123!"
        is_valid, errors = validate_password(no_uppercase)
        assert not is_valid
        assert "Password must contain at least one uppercase letter" in errors

    def test_no_digit(self):
        """Test that a password without digits fails validation"""
        no_digit = "Password!"
        is_valid, errors = validate_password(no_digit)
        assert not is_valid
        assert "Password must contain at least one number" in errors

    def test_no_special_char(self):
        """Test that a password without special characters fails validation"""
        no_special = "Password123"
        is_valid, errors = validate_password(no_special)
        assert not is_valid
        assert "Password must contain at least one special character" in errors

    def test_multiple_errors(self):
        """Test that multiple validation errors are reported"""
        bad_password = "pass"
        is_valid, errors = validate_password(bad_password)
        assert not is_valid
        assert len(errors) == 4  # Should have 4 errors (length, uppercase, digit, special)

    def test_custom_min_length(self):
        """Test that custom minimum length is enforced"""
        password = "Pass1!"
        is_valid, errors = validate_password(password, min_length=6)
        assert not is_valid  # Still invalid due to other requirements
        assert "Password must be at least 6 characters long" not in errors

        is_valid, errors = validate_password(password, min_length=10)
        assert not is_valid
        assert "Password must be at least 10 characters long" in errors

    def test_get_password_requirements(self):
        """Test that password requirements are returned as a string"""
        requirements = get_password_requirements()
        assert isinstance(requirements, str)
        assert "8 characters" in requirements
        assert "lowercase" in requirements
        assert "uppercase" in requirements
        assert "number" in requirements
        assert "special character" in requirements

