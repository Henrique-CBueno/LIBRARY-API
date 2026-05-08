import pytest

from app.domain.books.repositories.book_repository import BookRepository
from tests.factories.author_factory import make_author
from tests.factories.book_factory import make_book


async def seed_books(db_session):
    active_author = make_author(name="Machado de Assis")
    inactive_author = make_author(name="Inactive Author", is_active=False)

    available_book = make_book(
        title="Dom Casmurro",
        isbn="isbn-available",
        category="Romance",
        total_copies=5,
        available_copies=2,
        author=active_author,
        author_id=active_author.id,
    )
    unavailable_book = make_book(
        title="Quincas Borba",
        isbn="isbn-unavailable",
        category="Romance",
        total_copies=1,
        available_copies=0,
        author=active_author,
        author_id=active_author.id,
    )
    inactive_book = make_book(
        title="Inactive Book",
        isbn="isbn-inactive-book",
        category="Archive",
        author=active_author,
        author_id=active_author.id,
        is_active=False,
    )
    book_from_inactive_author = make_book(
        title="Hidden By Author",
        isbn="isbn-hidden-author",
        category="Archive",
        author=inactive_author,
        author_id=inactive_author.id,
    )

    db_session.add_all(
        [
            active_author,
            inactive_author,
            available_book,
            unavailable_book,
            inactive_book,
            book_from_inactive_author,
        ]
    )
    await db_session.commit()

    return {
        "active_author": active_author,
        "available_book": available_book,
        "unavailable_book": unavailable_book,
        "inactive_book": inactive_book,
        "book_from_inactive_author": book_from_inactive_author,
    }


@pytest.mark.asyncio
async def test_repository_should_create_and_find_book(db_session):
    author = make_author()
    db_session.add(author)
    await db_session.commit()

    repository = BookRepository(db_session)
    book = make_book(
        isbn="isbn-create",
        author=author,
        author_id=author.id,
    )

    created_book = await repository.create(book)
    found_by_isbn = await repository.find_by_isbn("isbn-create")
    found_by_id = await repository.find_by_id(created_book.id)

    assert created_book.id == book.id
    assert found_by_isbn.id == book.id
    assert found_by_id.id == book.id
    assert found_by_id.author.name == author.name


@pytest.mark.asyncio
async def test_repository_should_filter_only_active_books(db_session):
    data = await seed_books(db_session)
    repository = BookRepository(db_session)

    books, total = await repository.list_books_paginated(
        page=1,
        size=10,
    )

    assert total == 2
    assert {book.id for book in books} == {
        data["available_book"].id,
        data["unavailable_book"].id,
    }


@pytest.mark.asyncio
async def test_repository_should_filter_by_title_category_and_author(
    db_session,
):
    data = await seed_books(db_session)
    repository = BookRepository(db_session)

    books, total = await repository.list_books_paginated(
        page=1,
        size=10,
        title="Dom",
        category="Romance",
        author="Machado",
    )

    assert total == 1
    assert books[0].id == data["available_book"].id


@pytest.mark.asyncio
async def test_repository_should_filter_unavailable_books(db_session):
    data = await seed_books(db_session)
    repository = BookRepository(db_session)

    books, total = await repository.list_books_paginated(
        page=1,
        size=10,
        available=False,
    )

    assert total == 1
    assert books[0].id == data["unavailable_book"].id


@pytest.mark.asyncio
async def test_repository_should_not_find_inactive_book(db_session):
    data = await seed_books(db_session)
    repository = BookRepository(db_session)

    inactive_book = await repository.find_by_id(
        data["inactive_book"].id
    )
    hidden_by_author = await repository.find_by_id(
        data["book_from_inactive_author"].id
    )

    assert inactive_book is None
    assert hidden_by_author is None


@pytest.mark.asyncio
async def test_repository_should_update_book(db_session):
    data = await seed_books(db_session)
    repository = BookRepository(db_session)
    book = data["available_book"]
    book.title = "Updated Title"

    updated_book = await repository.update(book)

    assert updated_book.title == "Updated Title"


@pytest.mark.asyncio
async def test_repository_should_soft_delete_book(db_session):
    data = await seed_books(db_session)
    repository = BookRepository(db_session)
    book = data["available_book"]

    await repository.soft_delete(book)

    deleted_book = await repository.find_by_id(book.id)

    assert book.is_active is False
    assert deleted_book is None
