from tests.factories.book_factory import make_book_payload


async def create_book(
    client,
    author_id: str,
    title: str = "Dom Casmurro",
    category: str = "Romance",
    total_copies: int = 5,
    isbn: str | None = None,
):
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
