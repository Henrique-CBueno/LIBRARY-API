from datetime import datetime
from unittest.mock import AsyncMock

import pytest

from app.domain.books.schemas.book_schema import CreateBookSchema, UpdateBookSchema
from app.domain.books.services.book_service import BookService
from app.exceptions.base import BusinessRuleException, NotFoundException
from tests.factories.author_factory import make_author
from tests.factories.book_factory import make_book


def make_service():
    repository = AsyncMock()
    author_repository = AsyncMock()
    cache_service = AsyncMock()
    cache_service.get.return_value = None

    return (
        BookService(
            repository,
            author_repository,
            cache_service,
        ),
        repository,
        author_repository,
        cache_service,
    )


@pytest.mark.asyncio
async def test_should_not_create_duplicate_book():
    service, repository, author_repository, cache_service = make_service()
    repository.find_by_isbn.return_value = True

    with pytest.raises(BusinessRuleException):
        await service.create_book(
            CreateBookSchema(
                title="Dom Casmurro",
                isbn="123",
                category="Romance",
                total_copies=5,
                author_id="author-id",
            )
        )

    author_repository.find_by_id.assert_not_awaited()
    repository.create.assert_not_awaited()
    cache_service.delete_pattern.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_not_create_book_without_active_author():
    service, repository, author_repository, cache_service = make_service()
    repository.find_by_isbn.return_value = None
    author_repository.find_by_id.return_value = None

    with pytest.raises(NotFoundException):
        await service.create_book(
            CreateBookSchema(
                title="Dom Casmurro",
                isbn="123",
                category="Romance",
                total_copies=5,
                author_id="author-id",
            )
        )

    repository.create.assert_not_awaited()
    cache_service.delete_pattern.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_create_book_with_total_copies_available():
    service, repository, author_repository, cache_service = make_service()
    author = make_author()
    created_book = make_book(
        author_id=author.id,
        author=author,
        total_copies=4,
        available_copies=4,
    )

    repository.find_by_isbn.return_value = None
    author_repository.find_by_id.return_value = author
    repository.create.return_value = created_book

    response = await service.create_book(
        CreateBookSchema(
            title=created_book.title,
            isbn=created_book.isbn,
            category=created_book.category,
            total_copies=4,
            author_id=author.id,
        )
    )

    saved_book = repository.create.await_args.args[0]

    assert saved_book.available_copies == 4
    assert response["author"]["id"] == author.id
    assert response["total_copies"] == 4
    await cache_service.delete_pattern("books:list*")


@pytest.mark.asyncio
async def test_should_return_cached_book_list():
    service, repository, _, cache_service = make_service()
    cached_response = {
        "items": [],
        "total": 0,
        "page": 1,
        "size": 10,
    }
    cache_service.get.return_value = cached_response

    response = await service.list_books_paginated(1, 10)

    assert response == cached_response
    repository.list_books_paginated.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_list_books_and_cache_response():
    service, repository, _, cache_service = make_service()
    author = make_author()
    book = make_book(author=author, author_id=author.id)
    cache_service.get.return_value = None
    repository.list_books_paginated.return_value = ([book], 1)

    response = await service.list_books_paginated(
        page=1,
        size=10,
        title="Dom",
        category="Romance",
        author="Machado",
        available=True,
    )

    assert response["total"] == 1
    assert response["items"][0]["id"] == str(book.id)
    assert response["items"][0]["author"]["name"] == author.name
    cache_service.set.assert_awaited_once()


@pytest.mark.asyncio
async def test_should_raise_not_found_when_book_does_not_exist():
    service, repository, _, _ = make_service()
    repository.find_by_id.return_value = None

    with pytest.raises(NotFoundException):
        await service.get_book("book-id")


@pytest.mark.asyncio
async def test_should_return_cached_book():
    service, repository, _, cache_service = make_service()
    cached_book = {
        "id": "book-id",
        "title": "Dom Casmurro",
        "created_at": datetime.utcnow().isoformat(),
    }
    cache_service.get.return_value = cached_book

    response = await service.get_book("book-id")

    assert response == cached_book
    repository.find_by_id.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_get_book_and_cache_response():
    service, repository, _, cache_service = make_service()
    author = make_author()
    book = make_book(author=author, author_id=author.id)
    repository.find_by_id.return_value = book

    response = await service.get_book(book.id)

    assert response["id"] == str(book.id)
    assert response["author"]["id"] == str(author.id)
    cache_service.set.assert_awaited_once()


@pytest.mark.asyncio
async def test_should_raise_not_found_when_updating_missing_book():
    service, repository, _, _ = make_service()
    repository.find_by_id.return_value = None

    with pytest.raises(NotFoundException):
        await service.update_book(
            "book-id",
            UpdateBookSchema(title="New title"),
        )


@pytest.mark.asyncio
async def test_should_not_reduce_total_copies_below_borrowed_books():
    service, repository, _, _ = make_service()
    book = make_book(total_copies=5, available_copies=2)
    repository.find_by_id.return_value = book

    with pytest.raises(BusinessRuleException):
        await service.update_book(
            book.id,
            UpdateBookSchema(total_copies=1),
        )


@pytest.mark.asyncio
async def test_should_update_total_and_available_copies():
    service, repository, _, cache_service = make_service()
    book = make_book(total_copies=5, available_copies=3)
    repository.find_by_id.return_value = book
    repository.update.return_value = book

    updated_book = await service.update_book(
        book.id,
        UpdateBookSchema(
            title="Memorias Postumas",
            category="Classic",
            total_copies=7,
        ),
    )

    assert updated_book.title == "Memorias Postumas"
    assert updated_book.category == "Classic"
    assert updated_book.total_copies == 7
    assert updated_book.available_copies == 5
    cache_service.delete.assert_awaited_once_with(f"book:{book.id}")
    cache_service.delete_pattern.assert_awaited_once_with("books:list*")


@pytest.mark.asyncio
async def test_should_raise_not_found_when_deleting_missing_book():
    service, repository, _, _ = make_service()
    repository.find_by_id.return_value = None

    with pytest.raises(NotFoundException):
        await service.delete_book("book-id")


@pytest.mark.asyncio
async def test_should_soft_delete_book():
    service, repository, _, cache_service = make_service()
    book = make_book()
    repository.find_by_id.return_value = book

    await service.delete_book(book.id)

    repository.soft_delete.assert_awaited_once_with(book)
    cache_service.delete.assert_awaited_once_with(f"book:{book.id}")
    cache_service.delete_pattern.assert_awaited_once_with("books:list*")
