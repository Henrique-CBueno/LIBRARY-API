from tests.helpers.book_helper import create_book
from tests.helpers.user_helper import create_user


async def create_loan(
    client,
    user_id: str | None = None,
    book_id: str | None = None,
):
    user = None
    book = None

    if not user_id:
        user = await create_user(client)
        user_id = user["id"]

    if not book_id:
        book = await create_book(client)
        book_id = book["id"]

    response = await client.post(
        "/loans",
        json={
            "user_id": user_id,
            "book_id": book_id,
        },
    )

    assert response.status_code == 201

    return response.json()