import pytest
from pydantic import ValidationError

from app.schemas.user_schema import UserSignup


def test_role_sent_by_client_is_ignored():
    # Pydantic drops unknown fields, so "role" never reaches the database code
    signup = UserSignup(
        email="patient@example.com",
        password="securepass123",
        full_name="Test Patient",
        role="admin",
    )
    assert not hasattr(signup, "role")


def test_short_password_is_rejected():
    with pytest.raises(ValidationError):
        UserSignup(email="patient@example.com", password="short", full_name="Test")