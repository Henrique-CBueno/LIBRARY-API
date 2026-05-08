from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_service import CacheService
from app.domain.authors.repositories.author_repository import AuthorRepository
from app.domain.books.repositories.book_repository import BookRepository
from app.domain.books.schemas.book_schema import BookResponseSchema, CreateBookSchema
from app.domain.books.services.book_service import BookService
from app.infra.database.session import get_db

router = APIRouter(
    prefix="/books",
    tags=["Books"],
)


def get_book_service(
    db: AsyncSession = Depends(get_db),
):
    repository = BookRepository(db)

    author_repository = AuthorRepository(db)

    cache_service = CacheService()

    return BookService(
        repository,
        author_repository,
        cache_service,
    )


@router.post(
    "",
    response_model=BookResponseSchema,
    status_code=201,
)
async def create_book(
    data: CreateBookSchema,
    service: BookService = Depends(
        get_book_service
    ),
):
    return await service.create_book(data)


@router.get("")
async def list_books(
    title: str | None = Query(None),
    category: str | None = Query(None),
    service: BookService = Depends(
        get_book_service
    ),
):
    return await service.list_books(
        title,
        category,
    )


@router.get("/{book_id}")
async def get_book(
    book_id: UUID,
    service: BookService = Depends(
        get_book_service
    ),
):
    return await service.get_book(
        book_id
    )