import jwt
from datetime import datetime, timedelta, timezone

from app.config.app.settings import get_settings

settings = get_settings()


def create_access_token(
    user_id: str,
):
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.JWT_EXPIRE_MINUTES
    )

    payload = {
        "sub": user_id,
        "exp": expire,
    }

    return jwt.encode(
        payload,
        settings.JWT_SECRET,
        algorithm="HS256",
    )


def decode_token(token: str):
    return jwt.decode(
        token,
        settings.JWT_SECRET,
        algorithms=["HS256"],
    )