from app.schemas.user_schema import UserSignup, UserLogin

# Valid signup data
valid = UserSignup(
    email="test@example.com",
    password="securepass123",
    full_name="Test Patient",
    role="patient"
)
print("Valid signup:", valid)

# Invalid email - should raise an error
try:
    UserSignup(email="notanemail", password="securepass123", full_name="Test")
except Exception as e:
    print("Correctly rejected invalid email:", type(e).__name__)

# Invalid role - should raise an error
try:
    UserSignup(email="test@example.com", password="securepass123", full_name="Test", role="superadmin")
except Exception as e:
    print("Correctly rejected invalid role:", type(e).__name__)