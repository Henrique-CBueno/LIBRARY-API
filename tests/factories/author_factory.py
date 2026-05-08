import uuid6 as uuid

from app.domain.authors.models.author_model import AuthorModel


def make_author(
    name: str = "Machado de Assis",
    biography: str | None = "Brazilian author",
    is_active: bool = True,
):
    return AuthorModel(
        id=str(uuid.uuid7()),
        name=name,
        biography=biography,
        is_active=is_active,
    )


def make_author_payload(
    name: str = "Machado de Assis",
    biography: str | None = "Brazilian author",
):
    return {
        "name": name,
        "biography": biography,
    }
