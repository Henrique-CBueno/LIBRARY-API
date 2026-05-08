from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr


class CreateUserSchema(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserResponseSchema(BaseModel):
    id: UUID
    name: str
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateUserSchema(BaseModel):
    name: str | None = None


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class TokenResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
