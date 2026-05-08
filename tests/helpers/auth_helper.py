async def authenticate_user(
    client,
    email: str,
    password: str,
):
    response = await client.post(
        "/users/login",
        json={
            "email": email,
            "password": password,
        },
    )

    body = response.json()

    return body["access_token"]


async def auth_headers_for_user(
    client,
    email: str,
    password: str = "123456",
):
    token = await authenticate_user(
        client,
        email,
        password,
    )

    return {"Authorization": f"Bearer {token}"}
