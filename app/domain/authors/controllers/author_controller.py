from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_service import CacheService
from app.domain.authors.repositories.author_repository import AuthorRepository
from app.domain.authors.schemas.author_schema import AuthorResponseSchema, CreateAuthorSchema, UpdateAuthorSchema
from app.domain.authors.services.author_service import AuthorService
from app.infra.database.session import get_db

router = APIRouter(
    prefix="/authors",
    tags=["Authors"],
)


def get_author_service(
    db: AsyncSession = Depends(get_db),
):
    repository = AuthorRepository(db)

    cache_service = CacheService()

    return AuthorService(
        repository,
        cache_service,
    )


@router.post(
    "",
    response_model=AuthorResponseSchema,
    status_code=201,
)
async def create_author(
    data: CreateAuthorSchema,
    service: AuthorService = Depends(
        get_author_service
    ),
):
    return await service.create_author(data)


@router.get(
    "/{author_id}",
    response_model=AuthorResponseSchema,
)
async def get_author(
    author_id: str,
    service: AuthorService = Depends(
        get_author_service
    ),
):
    return await service.get_author(author_id)


@router.put(
    "/{author_id}",
    response_model=AuthorResponseSchema,
)
async def update_author(
    author_id: str,
    data: UpdateAuthorSchema,
    service: AuthorService = Depends(
        get_author_service
    ),
):
    return await service.update_author(
        author_id,
        data,
    )


@router.delete(
    "/{author_id}",
    status_code=204,
)
async def delete_author(
    author_id: str,
    service: AuthorService = Depends(
        get_author_service
    ),
):
    await service.delete_author(author_id)
