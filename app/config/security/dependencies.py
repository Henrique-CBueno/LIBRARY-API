from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials
from fastapi.security import HTTPBearer
import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.security.jwt import decode_token
from app.domain.users.repositories.user_repository import UserRepository
from app.exceptions.base import NotFoundException, UnauthorizedException
from app.infra.database.session import get_db
from app.domain.users.enums.user_role import UserRole

security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    token = credentials.credentials

    try:
        payload = decode_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise UnauthorizedException("Token expirado") from exc
    except jwt.PyJWTError as exc:
        raise UnauthorizedException("Token inválido") from exc

    user_id = payload.get("sub")

    repository = UserRepository(db)

    user = await repository.find_by_id(user_id)

    if not user:
        raise NotFoundException("Usuário não encontrado")

    return user


async def get_current_admin(
    current_user=Depends(get_current_user),
):
    if current_user.role != UserRole.ADMIN.value:
        raise UnauthorizedException("Acesso de administrador obrigatório")

    return current_user
