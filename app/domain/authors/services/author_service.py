from app.domain.authors.models.author_model import AuthorModel
from app.domain.authors.repositories.author_repository import AuthorRepository
from app.domain.authors.schemas.author_schema import CreateAuthorSchema


class AuthorService:

    def __init__(
        self,
        repository: AuthorRepository,
    ):
        self.repository = repository

    async def create_author(
        self,
        data: CreateAuthorSchema,
    ):
        author = AuthorModel(
            name=data.name,
            biography=data.biography,
        )

        return await self.repository.create(
            author
        )