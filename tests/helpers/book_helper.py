from tests.factories.book_factory import make_book_payload
from tests.helpers.author_helper import create_author


async def create_book(
    client,
    author_id: str | None = None,
    title: str = "Dom Casmurro",
    category: str = "Romance",
    total_copies: int = 5,
    isbn: str | None = None,
):
    if not author_id:
        author = await create_author(client)
        author_id = author["id"]

    response = await client.post(
        "/books",
        json=make_book_payload(
            title=title,
            isbn=isbn,
            category=category,
            total_copies=total_copies,
            author_id=author_id,
        ),
    )

    assert response.status_code == 201

    return response.json()
