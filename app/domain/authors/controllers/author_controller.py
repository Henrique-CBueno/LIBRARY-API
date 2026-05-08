from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.authors.repositories.author_repository import AuthorRepository
from app.domain.authors.schemas.author_schema import AuthorResponseSchema, CreateAuthorSchema
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

    return AuthorService(repository)


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