from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.cache.redis_service import CacheService
from app.config.security.dependencies import get_current_admin
from app.domain.authors.repositories.author_repository import AuthorRepository
from app.domain.books.repositories.book_repository import BookRepository
from app.domain.books.schemas.book_schema import BookResponseSchema, CreateBookSchema, UpdateBookSchema
from app.domain.books.services.book_service import BookService
from app.infra.database.session import get_db
from app.infra.padronize.pagination.schemas import PaginatedResponse

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
    _current_admin=Depends(get_current_admin),
):
    return await service.create_book(data)


@router.get(
    "",
    response_model=PaginatedResponse[
        BookResponseSchema
    ],
    summary="List books",
    description="Returns paginated books",
)
async def list_books(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    title: str | None = Query(None),
    category: str | None = Query(None),
    author: str | None = Query(None),
    available: bool | None = Query(None),
    service: BookService = Depends(
        get_book_service
    ),
):
    return await service.list_books_paginated(
        page,
        size,
        title,
        category,
        author,
        available,
    )


@router.get("/{book_id}")
async def get_book(
    book_id: str,
    service: BookService = Depends(
        get_book_service
    ),
):
    return await service.get_book(
        book_id
    )

@router.put(
    "/{book_id}",
    response_model=BookResponseSchema,
    summary="Update book",
)
async def update_book(
    book_id: str,
    data: UpdateBookSchema,
    service: BookService = Depends(
        get_book_service
    ),
    _current_admin=Depends(get_current_admin),
):
    return await service.update_book(
        book_id,
        data,
    )


@router.delete(
    "/{book_id}",
    status_code=204,
)
async def delete_book(
    book_id: str,
    service: BookService = Depends(
        get_book_service
    ),
    _current_admin=Depends(get_current_admin),
):
    await service.delete_book(book_id)
