#!/usr/bin/env python3
import bcrypt

def generate_hash(password):
    """Generate a bcrypt hash for the given password."""
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt(12)  # Using 12 rounds for security
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

if __name__ == "__main__":
    password = "World!"
    hashed_password = generate_hash(password)
    
    print(f"Password: {password}")
    print(f"Bcrypt Hash: {hashed_password}")