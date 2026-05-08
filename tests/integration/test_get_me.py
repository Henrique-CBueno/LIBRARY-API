async def test_get_me(client):

    await client.post(
        "/users",
        json={
            "name": "Henrique",
            "email": "henrique@email.com",
            "password": "123456",
        },
    )

    login_response = await client.post(
        "/users/login",
        json={
            "email": "henrique@email.com",
            "password": "123456",
        },
    )

    token = login_response.json()["access_token"]

    response = await client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
