from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.users.repositories.user_repository import UserRepository
from app.domain.users.schemas.user_schema import UserResponseSchema, CreateUserSchema
from app.domain.users.services.user_service import UserService
from app.infra.database.session import get_db

router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


def get_user_service(
    db: AsyncSession = Depends(get_db),
):
    repository = UserRepository(db)

    return UserService(repository)


@router.post(
    "",
    response_model=UserResponseSchema,
    status_code=201,
)
async def create_user(
    data: CreateUserSchema,
    service: UserService = Depends(get_user_service),
):
    return await service.create_user(data)


@router.get(
    "",
    response_model=list[UserResponseSchema],
)
async def list_users(
    service: UserService = Depends(get_user_service),
):
    return await service.list_users()