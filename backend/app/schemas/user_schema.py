from pydantic import BaseModel, EmailStr, Field
from datetime import datetime


class UserSignup(BaseModel):
    """Data required to create a new account."""
    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=100)
    role: str = Field(default="patient", pattern="^(patient|admin)$")


class UserLogin(BaseModel):
    """Data required to log in."""
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User data safe to return to the frontend (never includes password)."""
    id: int
    email: str
    full_name: str
    role: str
    created_at: datetime

    class Config:
        from_attributes = True  # allows creating this from a SQLAlchemy model directly


class Token(BaseModel):
    """Shape of the response after a successful login."""
    access_token: str
    token_type: str = "bearer"
    user: UserResponse