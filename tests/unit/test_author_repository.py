import pytest

from app.domain.authors.repositories.author_repository import AuthorRepository
from app.domain.books.repositories.book_repository import BookRepository
from tests.factories.author_factory import make_author
from tests.factories.book_factory import make_book


async def seed_author_with_books(db_session):
    author = make_author(name="Machado de Assis")
    inactive_author = make_author(
        name="Inactive Author",
        is_active=False,
    )
    active_book = make_book(
        title="Dom Casmurro",
        author=author,
        author_id=author.id,
    )
    inactive_book = make_book(
        title="Archived Book",
        author=author,
        author_id=author.id,
        is_active=False,
    )

    db_session.add_all(
        [
            author,
            inactive_author,
            active_book,
            inactive_book,
        ]
    )
    await db_session.commit()

    return {
        "author": author,
        "inactive_author": inactive_author,
        "active_book": active_book,
        "inactive_book": inactive_book,
    }


@pytest.mark.asyncio
async def test_repository_should_create_and_find_author(db_session):
    repository = AuthorRepository(db_session)
    author = make_author(name="Clarice Lispector")

    created_author = await repository.create(author)
    found_author = await repository.find_by_id(created_author.id)

    assert created_author.id == author.id
    assert found_author.id == author.id
    assert found_author.name == "Clarice Lispector"


@pytest.mark.asyncio
async def test_repository_should_not_find_inactive_author(db_session):
    data = await seed_author_with_books(db_session)
    repository = AuthorRepository(db_session)

    author = await repository.find_by_id(
        data["inactive_author"].id
    )

    assert author is None


@pytest.mark.asyncio
async def test_repository_should_find_author_with_books(db_session):
    data = await seed_author_with_books(db_session)
    repository = AuthorRepository(db_session)

    author = await repository.find_by_id_with_books(
        data["author"].id
    )

    assert author.id == data["author"].id
    assert {book.id for book in author.books} == {
        data["active_book"].id,
        data["inactive_book"].id,
    }


@pytest.mark.asyncio
async def test_repository_should_not_find_inactive_author_with_books(
    db_session,
):
    data = await seed_author_with_books(db_session)
    repository = AuthorRepository(db_session)

    author = await repository.find_by_id_with_books(
        data["inactive_author"].id
    )

    assert author is None


@pytest.mark.asyncio
async def test_repository_should_update_author(db_session):
    data = await seed_author_with_books(db_session)
    repository = AuthorRepository(db_session)
    author = data["author"]
    author.name = "Updated Author"
    author.biography = None

    updated_author = await repository.update(author)

    assert updated_author.name == "Updated Author"
    assert updated_author.biography is None


@pytest.mark.asyncio
async def test_repository_should_soft_delete_author_and_active_books(
    db_session,
):
    data = await seed_author_with_books(db_session)
    author_repository = AuthorRepository(db_session)
    book_repository = BookRepository(db_session)
    author = await author_repository.find_by_id_with_books(
        data["author"].id
    )

    await author_repository.soft_delete(author)

    deleted_author = await author_repository.find_by_id(
        data["author"].id
    )
    active_book = await book_repository.find_by_id(
        data["active_book"].id
    )
    inactive_book = await book_repository.find_by_id(
        data["inactive_book"].id
    )

    assert author.is_active is False
    assert deleted_author is None
    assert active_book is None
    assert inactive_book is None
    assert data["inactive_book"].is_active is False
