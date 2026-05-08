from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.security.dependencies import get_current_user, get_current_admin
from app.domain.users.repositories.user_repository import UserRepository
from app.domain.users.schemas.user_schema import (
    UserResponseSchema,
    CreateUserSchema,
    TokenResponseSchema,
    LoginSchema,
    UpdateUserSchema,
    UpdateUserRoleSchema,
)
from app.domain.users.services.user_service import UserService
from app.infra.database.session import get_db
from app.infra.middleware.rate_limit import limiter
from app.infra.padronize.pagination.schemas import PaginatedResponse

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
@limiter.limit("10/minute")
async def create_user(
    request: Request,
    data: CreateUserSchema,
    service: UserService = Depends(get_user_service),
):
    return await service.create_user(data)


@router.get(
    "",
    response_model=PaginatedResponse[UserResponseSchema],
)
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    service: UserService = Depends(get_user_service),
    _current_admin=Depends(get_current_admin),
):
    return await service.list_users_paginated(
        page,
        size,
    )


@router.post(
    "/login",
    response_model=TokenResponseSchema,
)
@limiter.limit("5/minute")
async def login(
    request: Request,
    data: LoginSchema,
    service: UserService = Depends(get_user_service),
):
    return await service.login(data)


@router.get(
    "/me",
    response_model=UserResponseSchema,
)
async def me(
    current_user=Depends(get_current_user),
):
    return current_user


@router.get(
    "/{user_id}",
    response_model=UserResponseSchema,
)
async def get_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
    _current_admin=Depends(get_current_admin),
):
    return await service.get_by_id(user_id)


@router.put(
    "/{user_id}",
    response_model=UserResponseSchema,
)
async def update_user(
    user_id: str,
    data: UpdateUserSchema,
    service: UserService = Depends(get_user_service),
    _current_admin=Depends(get_current_admin),
):
    return await service.update_user(
        user_id,
        data,
    )


@router.delete(
    "/{user_id}",
    status_code=204,
)
async def delete_user(
    user_id: str,
    service: UserService = Depends(get_user_service),
    _current_admin=Depends(get_current_admin),
):
    await service.delete_user(user_id)


@router.put(
    "/{user_id}/role",
    status_code=204,
)
async def update_user_role(
    user_id: str,
    data: UpdateUserRoleSchema,
    service: UserService = Depends(get_user_service),
    _current_admin=Depends(get_current_admin),
):
    await service.update_role(user_id, data)
