from datetime import datetime

import uuid6 as uuid

from app.domain.books.models.book_model import BookModel


def make_book(
    title: str = "Dom Casmurro",
    isbn: str | None = None,
    category: str = "Romance",
    total_copies: int = 5,
    available_copies: int | None = None,
    author_id: str | None = None,
    author=None,
    is_active: bool = True,
):
    return BookModel(
        id=str(uuid.uuid7()),
        title=title,
        isbn=isbn or str(uuid.uuid7()),
        category=category,
        total_copies=total_copies,
        available_copies=(
            total_copies
            if available_copies is None
            else available_copies
        ),
        author_id=author_id or str(uuid.uuid7()),
        author=author,
        created_at=datetime.utcnow(),
        is_active=is_active,
    )


def make_book_payload(
    title: str = "Dom Casmurro",
    isbn: str | None = None,
    category: str = "Romance",
    total_copies: int = 5,
    author_id: str | None = None,
):
    return {
        "title": title,
        "isbn": isbn or str(uuid.uuid7()),
        "category": category,
        "total_copies": total_copies,
        "author_id": author_id or str(uuid.uuid7()),
    }
