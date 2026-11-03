"""Request and response shapes for user accounts."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UserSignup(BaseModel):
    """Data required to create a new patient account. The role is never accepted from the client."""

    email: EmailStr
    password: str = Field(min_length=8, max_length=72)
    full_name: str = Field(min_length=1, max_length=100)


class UserLogin(BaseModel):
    """Data required to log in."""

    email: EmailStr
    password: str


class UserResponse(BaseModel):
    """User data safe to return to the frontend. Never includes the password."""

    id: int
    email: str
    full_name: str
    role: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Shape of the response after a successful login."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse