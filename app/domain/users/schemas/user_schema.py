from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.domain.users.enums.user_role import UserRole


class CreateUserSchema(BaseModel):
    name: str
    email: EmailStr
    password: str


class UserResponseSchema(BaseModel):
    id: str
    name: str
    email: EmailStr
    created_at: datetime

    model_config = {"from_attributes": True}


class UpdateUserSchema(BaseModel):
    name: str | None = None


class UpdateUserRoleSchema(BaseModel):
    role: UserRole


class LoginSchema(BaseModel):
    email: EmailStr
    password: str


class TokenResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"
