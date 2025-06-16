#!/usr/bin/env python3
"""
Generate a bcrypt hash for the initial user password.
This script creates a proper bcrypt hash for the 'Hello' user's password 'World!'.
"""

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
    
    print("\nCypher for init-db.cypher:")
    print(f"MERGE (u:User {{")
    print(f"    username: 'Hello',")
    print(f"    password_hash: '{hashed_password}',")
    print(f"    role: 'Greeter',")
    print(f"    created_at: datetime()")
    print(f"}});")