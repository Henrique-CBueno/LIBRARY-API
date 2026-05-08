import pytest
from sqlalchemy import update

from app.cache.redis_service import CacheService
from app.domain.books.models.book_model import BookModel
from tests.factories.author_factory import make_author_payload
from tests.factories.book_factory import make_book_payload


@pytest.fixture(autouse=True)
def disable_book_cache(monkeypatch):
    async def get(self, key):
        return None

    async def set(self, key, value, expire=300):
        return None

    async def delete(self, key):
        return None

    async def delete_pattern(self, pattern):
        return None

    monkeypatch.setattr(CacheService, "get", get)
    monkeypatch.setattr(CacheService, "set", set)
    monkeypatch.setattr(CacheService, "delete", delete)
    monkeypatch.setattr(CacheService, "delete_pattern", delete_pattern)


async def create_author(client, name="Machado de Assis"):
    response = await client.post(
        "/authors",
        json=make_author_payload(name=name),
    )

    assert response.status_code == 201

    return response.json()


async def create_book(
    client,
    author_id,
    title="Dom Casmurro",
    category="Romance",
    total_copies=5,
):
    response = await client.post(
        "/books",
        json=make_book_payload(
            title=title,
            category=category,
            total_copies=total_copies,
            author_id=author_id,
        ),
    )

    assert response.status_code == 201

    return response.json()


async def test_should_create_book_with_author(client):
    author = await create_author(client)

    response = await client.post(
        "/books",
        json=make_book_payload(
            title="Dom Casmurro",
            category="Romance",
            total_copies=3,
            author_id=author["id"],
        ),
    )

    assert response.status_code == 201

    body = response.json()

    assert body["title"] == "Dom Casmurro"
    assert body["total_copies"] == 3
    assert body["available_copies"] == 3
    assert body["author"]["id"] == author["id"]


async def test_should_not_create_duplicate_isbn(client):
    author = await create_author(client)
    payload = make_book_payload(author_id=author["id"])

    await client.post("/books", json=payload)

    response = await client.post("/books", json=payload)

    assert response.status_code == 400
    assert response.json()["error"]["message"] == "ISBN already exists"


async def test_should_not_create_book_with_missing_author(client):
    payload = make_book_payload(
        author_id="00000000-0000-0000-0000-000000000000"
    )

    response = await client.post("/books", json=payload)

    assert response.status_code == 404
    assert response.json()["error"]["message"] == "Author not found"


async def test_should_paginate_and_filter_books(client):
    author = await create_author(client, name="Machado de Assis")
    other_author = await create_author(client, name="Clarice Lispector")

    await create_book(
        client,
        author["id"],
        title="Dom Casmurro",
        category="Romance",
    )
    await create_book(
        client,
        author["id"],
        title="Quincas Borba",
        category="Romance",
    )
    await create_book(
        client,
        other_author["id"],
        title="A Hora da Estrela",
        category="Novel",
    )

    response = await client.get(
        "/books?page=1&size=10&category=Romance&author=Machado"
    )

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 2
    assert body["page"] == 1
    assert body["size"] == 10
    assert {item["title"] for item in body["items"]} == {
        "Dom Casmurro",
        "Quincas Borba",
    }


async def test_should_filter_available_books(client, db_session):
    author = await create_author(client)
    available_book = await create_book(
        client,
        author["id"],
        title="Available",
        total_copies=3,
    )
    unavailable_book = await create_book(
        client,
        author["id"],
        title="Unavailable",
        total_copies=1,
    )

    await db_session.execute(
        update(BookModel)
        .where(BookModel.id == unavailable_book["id"])
        .values(available_copies=0)
    )
    await db_session.commit()

    response = await client.get("/books?available=true")

    assert response.status_code == 200

    body = response.json()

    assert body["total"] == 1
    assert body["items"][0]["id"] == available_book["id"]


async def test_should_get_book_by_id(client):
    author = await create_author(client)
    book = await create_book(client, author["id"])

    response = await client.get(f"/books/{book['id']}")

    assert response.status_code == 200

    body = response.json()

    assert body["id"] == book["id"]
    assert body["author"]["id"] == author["id"]


async def test_should_update_book(client):
    author = await create_author(client)
    book = await create_book(client, author["id"], total_copies=5)

    response = await client.put(
        f"/books/{book['id']}",
        json={
            "title": "Memorias Postumas de Bras Cubas",
            "category": "Classic",
            "total_copies": 7,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["title"] == "Memorias Postumas de Bras Cubas"
    assert body["category"] == "Classic"
    assert body["total_copies"] == 7
    assert body["available_copies"] == 7


async def test_should_not_reduce_total_below_borrowed_books(
    client,
    db_session,
):
    author = await create_author(client)
    book = await create_book(client, author["id"], total_copies=5)

    await db_session.execute(
        update(BookModel)
        .where(BookModel.id == book["id"])
        .values(available_copies=2)
    )
    await db_session.commit()

    response = await client.put(
        f"/books/{book['id']}",
        json={"total_copies": 1},
    )

    assert response.status_code == 400
    assert (
        response.json()["error"]["message"]
        == "total_copies cannot be lower than borrowed books"
    )


async def test_should_soft_delete_book_and_hide_from_gets(client):
    author = await create_author(client)
    book = await create_book(client, author["id"])

    delete_response = await client.delete(f"/books/{book['id']}")

    assert delete_response.status_code == 204

    get_response = await client.get(f"/books/{book['id']}")
    list_response = await client.get("/books")

    assert get_response.status_code == 404
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 0


async def test_should_hide_books_when_author_is_inactive(client):
    author = await create_author(client)
    book = await create_book(client, author["id"])

    delete_author_response = await client.delete(f"/authors/{author['id']}")

    assert delete_author_response.status_code == 204

    get_response = await client.get(f"/books/{book['id']}")
    list_response = await client.get("/books")

    assert get_response.status_code == 404
    assert list_response.status_code == 200
    assert list_response.json()["total"] == 0
