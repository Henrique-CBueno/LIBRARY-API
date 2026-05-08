import uuid6 as uuid


async def create_user(
    client,
    name: str = "Henrique",
    email: str | None = None,
    password: str = "123456",
):
    response = await client.post(
        "/users",
        json={
            "name": name,
            "email": email or f"{uuid.uuid7()}@email.com",
            "password": password,
        },
    )

    assert response.status_code == 201

    return response.json()