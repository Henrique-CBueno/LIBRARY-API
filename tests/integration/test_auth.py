async def test_should_not_login_with_invalid_password(
    client,
):
    await client.post(
        "/users",
        json={
            "name": "Henrique",
            "email": "henrique@email.com",
            "password": "123456",
        },
    )

    response = await client.post(
        "/users/login",
        json={
            "email": "henrique@email.com",
            "password": "wrong-password",
        },
    )

    assert response.status_code == 400


async def test_should_not_access_protected_route_with_invalid_token(
    client,
):
    response = await client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code in [401, 403]


async def test_should_not_access_protected_route_without_token(
    anonymous_client,
):
    response = await anonymous_client.get("/users/me")

    assert response.status_code in [401, 403]
