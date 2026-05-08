import uuid6 as uuid

from app.config.security.hashing import hash_password
from app.domain.users.models.user_model import UserModel


def make_user(
    name: str = "Henrique",
    email: str | None = None,
    password: str = "123456",
):
    return UserModel(
        id=str(uuid.uuid7()),
        name=name,
        email=email or f"{uuid.uuid7()}@email.com",
        password=hash_password(password),
        is_active=True,
    )
