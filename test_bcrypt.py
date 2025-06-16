import bcrypt

# Test if bcrypt is working correctly
password = b"test_password"
salt = bcrypt.gensalt()
hashed = bcrypt.hashpw(password, salt)

print("bcrypt version:", bcrypt.__version__)
print("Salt generated:", salt)
print("Hashed password:", hashed)
print("Verification:", bcrypt.checkpw(password, hashed))