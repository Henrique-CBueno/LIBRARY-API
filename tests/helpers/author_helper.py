from tests.factories.author_factory import make_author_payload


async def create_author(
    client,
    name: str = "Machado de Assis",
    biography: str | None = "Brazilian author",
):
    response = await client.post(
        "/authors",
        json=make_author_payload(
            name=name,
            biography=biography,
        ),
    )

    assert response.status_code == 201

    return response.json()
