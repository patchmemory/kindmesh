"""
Password policy module for kindmesh application.
Contains functions for validating password strength and complexity.
"""

import re
from typing import Tuple, List

def validate_password(password: str, min_length: int = 8) -> Tuple[bool, List[str]]:
    """
    Validate a password against security policies.
    
    Args:
        password: The password to validate
        min_length: Minimum required password length (default: 8)
        
    Returns:
        Tuple containing:
            - bool: True if password meets all requirements, False otherwise
            - List[str]: List of validation error messages (empty if password is valid)
    """
    errors = []
    
    # Check minimum length
    if len(password) < min_length:
        errors.append(f"Password must be at least {min_length} characters long")
    
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        errors.append("Password must contain at least one lowercase letter")
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        errors.append("Password must contain at least one uppercase letter")
    
    # Check for at least one digit
    if not re.search(r'\d', password):
        errors.append("Password must contain at least one number")
    
    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Password must contain at least one special character")
    
    # Return validation result
    return len(errors) == 0, errors

def get_password_requirements() -> str:
    """
    Get a human-readable description of password requirements.
    
    Returns:
        str: Description of password requirements
    """
    return """
    Password must:
    - Be at least 8 characters long
    - Contain at least one lowercase letter
    - Contain at least one uppercase letter
    - Contain at least one number
    - Contain at least one special character (!@#$%^&*(),.?":{}|<>)
    """