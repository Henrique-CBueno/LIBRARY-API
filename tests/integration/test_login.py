async def test_login(client):

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
            "password": "123456",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert "access_token" in body
