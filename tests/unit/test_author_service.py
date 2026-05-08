from unittest.mock import AsyncMock

import pytest

from app.domain.authors.schemas.author_schema import CreateAuthorSchema, UpdateAuthorSchema
from app.domain.authors.services.author_service import AuthorService
from app.exceptions.base import NotFoundException
from tests.factories.author_factory import make_author
from tests.factories.book_factory import make_book


def make_service():
    repository = AsyncMock()
    cache_service = AsyncMock()

    return (
        AuthorService(
            repository,
            cache_service,
        ),
        repository,
        cache_service,
    )


@pytest.mark.asyncio
async def test_should_create_author():
    service, repository, _ = make_service()
    author = make_author()
    repository.create.return_value = author

    response = await service.create_author(
        CreateAuthorSchema(
            name=author.name,
            biography=author.biography,
        )
    )

    saved_author = repository.create.await_args.args[0]

    assert response == author
    assert saved_author.name == author.name
    assert saved_author.biography == author.biography


@pytest.mark.asyncio
async def test_should_get_author():
    service, repository, _ = make_service()
    author = make_author()
    repository.find_by_id.return_value = author

    response = await service.get_author(author.id)

    assert response == author
    repository.find_by_id.assert_awaited_once_with(author.id)


@pytest.mark.asyncio
async def test_should_raise_not_found_when_author_does_not_exist():
    service, repository, _ = make_service()
    repository.find_by_id.return_value = None

    with pytest.raises(NotFoundException):
        await service.get_author("author-id")


@pytest.mark.asyncio
async def test_should_update_author():
    service, repository, cache_service = make_service()
    author = make_author()
    repository.find_by_id.return_value = author
    repository.update.return_value = author

    response = await service.update_author(
        author.id,
        UpdateAuthorSchema(
            name="Clarice Lispector",
            biography="Updated biography",
        ),
    )

    assert response.name == "Clarice Lispector"
    assert response.biography == "Updated biography"
    repository.update.assert_awaited_once_with(author)
    cache_service.delete_pattern.assert_any_await("book:*")
    cache_service.delete_pattern.assert_any_await("books:list*")


@pytest.mark.asyncio
async def test_should_allow_author_biography_to_be_cleared():
    service, repository, _ = make_service()
    author = make_author(biography="Old biography")
    repository.find_by_id.return_value = author
    repository.update.return_value = author

    response = await service.update_author(
        author.id,
        UpdateAuthorSchema(biography=None),
    )

    assert response.biography is None


@pytest.mark.asyncio
async def test_should_raise_not_found_when_updating_missing_author():
    service, repository, _ = make_service()
    repository.find_by_id.return_value = None

    with pytest.raises(NotFoundException):
        await service.update_author(
            "author-id",
            UpdateAuthorSchema(name="New name"),
        )

    repository.update.assert_not_awaited()


@pytest.mark.asyncio
async def test_should_delete_author_and_clear_book_cache():
    service, repository, cache_service = make_service()
    author = make_author()
    author.books = [
        make_book(author=author, author_id=author.id),
    ]
    repository.find_by_id_with_books.return_value = author

    await service.delete_author(author.id)

    repository.soft_delete.assert_awaited_once_with(author)
    cache_service.delete_pattern.assert_any_await("book:*")
    cache_service.delete_pattern.assert_any_await("books:list*")


@pytest.mark.asyncio
async def test_should_raise_not_found_when_deleting_missing_author():
    service, repository, cache_service = make_service()
    repository.find_by_id_with_books.return_value = None

    with pytest.raises(NotFoundException):
        await service.delete_author("author-id")

    repository.soft_delete.assert_not_awaited()
    cache_service.delete_pattern.assert_not_awaited()
