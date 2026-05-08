import uuid6 as uuid

from app.config.security.hashing import hash_password
from app.domain.users.enums.user_role import UserRole
from app.domain.users.models.user_model import UserModel
from app.domain.users.repositories.user_repository import UserRepository
from tests.helpers.auth_helper import authenticate_user


async def _create_admin_user(
    db_session,
    email: str | None = None,
    password: str = "123456",
):
    user = UserModel(
        name="Admin",
        email=email or f"{uuid.uuid7()}@email.com",
        password=hash_password(password),
        is_active=True,
        role=UserRole.ADMIN.value,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user, password

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


async def test_should_allow_admin_to_promote_user(
    client,
    db_session,
):
    admin, admin_password = await _create_admin_user(db_session)

    token = await authenticate_user(
        client,
        admin.email,
        admin_password,
    )

    create_response = await client.post(
        "/users",
        json={
            "name": "User",
            "email": f"{uuid.uuid7()}@email.com",
            "password": "123456",
        },
    )

    assert create_response.status_code == 201

    user_id = create_response.json()["id"]

    response = await client.put(
        f"/users/{user_id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "ADMIN"},
    )

    assert response.status_code == 204

    repository = UserRepository(db_session)
    updated_user = await repository.find_by_id(user_id)

    assert updated_user.role == UserRole.ADMIN.value


async def test_should_forbid_non_admin_to_promote_user(
    client,
):
    email = f"{uuid.uuid7()}@email.com"

    await client.post(
        "/users",
        json={
            "name": "User",
            "email": email,
            "password": "123456",
        },
    )

    token = await authenticate_user(
        client,
        email,
        "123456",
    )

    create_response = await client.post(
        "/users",
        json={
            "name": "Other User",
            "email": f"{uuid.uuid7()}@email.com",
            "password": "123456",
        },
    )

    assert create_response.status_code == 201

    user_id = create_response.json()["id"]

    response = await client.put(
        f"/users/{user_id}/role",
        headers={"Authorization": f"Bearer {token}"},
        json={"role": "ADMIN"},
    )

    assert response.status_code == 401
