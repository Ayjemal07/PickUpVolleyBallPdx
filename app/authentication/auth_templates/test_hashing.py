# test_hashing.py
from werkzeug.security import generate_password_hash, check_password_hash

password = "testpassword"

# Get hashing method (adjust if you are explicitly setting a different one in your Flask app)
method = 'pbkdf2:sha256'  # This is a common and secure default

hashed_password = generate_password_hash(password, method=method)
print(f"Hashed password: {hashed_password}")

is_valid = check_password_hash(hashed_password, password)
print(f"Is password valid: {is_valid}")