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
