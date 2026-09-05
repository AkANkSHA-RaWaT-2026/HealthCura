from app.core.security import hash_password, verify_password, create_access_token, decode_access_token

# Test password hashing
plain = "mysecretpassword123"
hashed = hash_password(plain)
print("Hashed:", hashed)
print("Verify correct password:", verify_password(plain, hashed))
print("Verify wrong password:", verify_password("wrongpassword", hashed))

# Test JWT
token = create_access_token({"user_id": 1, "role": "patient"})
print("Token:", token)
print("Decoded:", decode_access_token(token))
print("Invalid token decode:", decode_access_token("not.a.valid.token"))