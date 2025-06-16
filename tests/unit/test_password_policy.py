import unittest

# Import the module to test
from app.password_policy import validate_password, get_password_requirements

class TestPasswordPolicy(unittest.TestCase):
    """Unit tests for the password policy module"""

    def test_valid_password(self):
        """Test that a valid password passes validation"""
        valid_password = "Password123!"
        is_valid, errors = validate_password(valid_password)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)
    
    def test_short_password(self):
        """Test that a short password fails validation"""
        short_password = "Pass1!"
        is_valid, errors = validate_password(short_password)
        self.assertFalse(is_valid)
        self.assertIn("Password must be at least 8 characters long", errors)
    
    def test_no_lowercase(self):
        """Test that a password without lowercase letters fails validation"""
        no_lowercase = "PASSWORD123!"
        is_valid, errors = validate_password(no_lowercase)
        self.assertFalse(is_valid)
        self.assertIn("Password must contain at least one lowercase letter", errors)
    
    def test_no_uppercase(self):
        """Test that a password without uppercase letters fails validation"""
        no_uppercase = "password123!"
        is_valid, errors = validate_password(no_uppercase)
        self.assertFalse(is_valid)
        self.assertIn("Password must contain at least one uppercase letter", errors)
    
    def test_no_digit(self):
        """Test that a password without digits fails validation"""
        no_digit = "Password!"
        is_valid, errors = validate_password(no_digit)
        self.assertFalse(is_valid)
        self.assertIn("Password must contain at least one number", errors)
    
    def test_no_special_char(self):
        """Test that a password without special characters fails validation"""
        no_special = "Password123"
        is_valid, errors = validate_password(no_special)
        self.assertFalse(is_valid)
        self.assertIn("Password must contain at least one special character", errors)
    
    def test_multiple_errors(self):
        """Test that multiple validation errors are reported"""
        bad_password = "pass"
        is_valid, errors = validate_password(bad_password)
        self.assertFalse(is_valid)
        self.assertEqual(len(errors), 4)  # Should have 4 errors (length, uppercase, digit, special)
    
    def test_custom_min_length(self):
        """Test that custom minimum length is enforced"""
        password = "Pass1!"
        is_valid, errors = validate_password(password, min_length=6)
        self.assertFalse(is_valid)  # Still invalid due to other requirements
        self.assertNotIn("Password must be at least 6 characters long", errors)
        
        is_valid, errors = validate_password(password, min_length=10)
        self.assertFalse(is_valid)
        self.assertIn("Password must be at least 10 characters long", errors)
    
    def test_get_password_requirements(self):
        """Test that password requirements are returned as a string"""
        requirements = get_password_requirements()
        self.assertIsInstance(requirements, str)
        self.assertIn("8 characters", requirements)
        self.assertIn("lowercase", requirements)
        self.assertIn("uppercase", requirements)
        self.assertIn("number", requirements)
        self.assertIn("special character", requirements)

if __name__ == '__main__':
    unittest.main()