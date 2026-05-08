async def test_should_not_create_duplicate_user(
    client,
):
    payload = {
        "name": "Henrique",
        "email": "henrique@email.com",
        "password": "123456",
    }

    await client.post(
        "/users",
        json=payload,
    )

    response = await client.post(
        "/users",
        json=payload,
    )

    assert response.status_code == 400

    body = response.json()

    assert body["error"]["message"] == "Email already exists"


async def test_should_return_404_when_user_not_found(
    client,
):
    response = await client.get("/users/00000000-0000-0000-0000-000000000000")

    assert response.status_code == 404


async def test_should_paginate_users(
    client,
):
    for i in range(15):
        await client.post(
            "/users",
            json={
                "name": f"User {i}",
                "email": f"user{i}@email.com",
                "password": "123456",
            },
        )

    response = await client.get("/users?page=1&size=10")

    assert response.status_code == 200

    body = response.json()

    assert len(body["items"]) == 10
    assert body["page"] == 1
    assert body["size"] == 10


async def test_should_update_user(
    client,
):
    create_response = await client.post(
        "/users",
        json={
            "name": "Henrique",
            "email": "henrique@email.com",
            "password": "123456",
        },
    )

    user_id = create_response.json()["id"]

    response = await client.put(
        f"/users/{user_id}",
        json={"name": "Novo Nome"},
    )

    assert response.status_code == 200

    body = response.json()

    assert body["name"] == "Novo Nome"


async def test_should_soft_delete_user(
    client,
):
    create_response = await client.post(
        "/users",
        json={
            "name": "Henrique",
            "email": "henrique@email.com",
            "password": "123456",
        },
    )

    user_id = create_response.json()["id"]

    response = await client.delete(f"/users/{user_id}")

    assert response.status_code == 204
