import pytest

from tests.helpers.author_helper import create_author
from tests.helpers.book_helper import create_book
from tests.helpers.cache_helper import disable_cache


@pytest.fixture(autouse=True)
def disable_author_cache(monkeypatch):
    disable_cache(monkeypatch)


async def test_should_create_author(client):
    response = await client.post(
        "/authors",
        json={
            "name": "Machado de Assis",
            "biography": "Brazilian author",
        },
    )

    assert response.status_code == 201

    body = response.json()

    assert body["name"] == "Machado de Assis"
    assert body["biography"] == "Brazilian author"
    assert body["created_at"]


async def test_should_get_author_by_id(client):
    author = await create_author(client)

    response = await client.get(f"/authors/{author['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == author["id"]


async def test_should_return_404_when_author_not_found(client):
    response = await client.get(
        "/authors/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Author not found"


async def test_should_update_author(client):
    author = await create_author(client)

    response = await client.put(
        f"/authors/{author['id']}",
        json={
            "name": "Clarice Lispector",
            "biography": "Updated biography",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["name"] == "Clarice Lispector"
    assert body["biography"] == "Updated biography"


async def test_should_clear_author_biography(client):
    author = await create_author(
        client,
        biography="Biography to clear",
    )

    response = await client.put(
        f"/authors/{author['id']}",
        json={"biography": None},
    )

    assert response.status_code == 200
    assert response.json()["biography"] is None


async def test_should_return_404_when_updating_missing_author(client):
    response = await client.put(
        "/authors/00000000-0000-0000-0000-000000000000",
        json={"name": "Missing Author"},
    )

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Author not found"


async def test_should_soft_delete_author_and_hide_from_get(client):
    author = await create_author(client)

    delete_response = await client.delete(f"/authors/{author['id']}")

    assert delete_response.status_code == 204

    get_response = await client.get(f"/authors/{author['id']}")
    update_response = await client.put(
        f"/authors/{author['id']}",
        json={"name": "Should not update"},
    )

    assert get_response.status_code == 404
    assert update_response.status_code == 404


async def test_should_soft_delete_author_books(client):
    author = await create_author(client)
    book = await create_book(client, author["id"])

    delete_response = await client.delete(f"/authors/{author['id']}")

    assert delete_response.status_code == 204

    get_book_response = await client.get(f"/books/{book['id']}")
    list_books_response = await client.get("/books")

    assert get_book_response.status_code == 404
    assert list_books_response.status_code == 200
    assert list_books_response.json()["total"] == 0


async def test_should_return_404_when_deleting_missing_author(client):
    response = await client.delete(
        "/authors/00000000-0000-0000-0000-000000000000"
    )

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Author not found"
