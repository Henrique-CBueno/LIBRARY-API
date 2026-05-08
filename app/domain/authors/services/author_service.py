from app.cache.redis_service import CacheService
from app.domain.authors.models.author_model import AuthorModel
from app.domain.authors.repositories.author_repository import AuthorRepository
from app.domain.authors.schemas.author_schema import CreateAuthorSchema, UpdateAuthorSchema
from app.exceptions.base import NotFoundException


class AuthorService:

    def __init__(
        self,
        repository: AuthorRepository,
        cache_service: CacheService,
    ):
        self.repository = repository
        self.cache_service = cache_service

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

    async def get_author(
        self,
        author_id: str,
    ):
        author = await self.repository.find_by_id(
            author_id
        )

        if not author:
            raise NotFoundException(
                "Author not found"
            )

        return author

    async def list_authors_paginated(
        self,
        page: int,
        size: int,
    ):
        authors, total = (
            await self.repository.list_authors_paginated(
                page,
                size,
            )
        )

        return {
            "items": authors,
            "total": total,
            "page": page,
            "size": size,
        }

    async def delete_author(
        self,
        author_id: str,
    ):
        author = (
            await self.repository.find_by_id_with_books(
                author_id
            )
        )

        if not author:
            raise NotFoundException(
                "Author not found"
            )

        await self.repository.soft_delete(author)

        await self.cache_service.delete_pattern(
            "book:*"
        )

        await self.cache_service.delete_pattern(
            "books:list*"
        )

    async def update_author(
        self,
        author_id: str,
        data: UpdateAuthorSchema,
    ):
        author = await self.repository.find_by_id(
            author_id
        )

        if not author:
            raise NotFoundException(
                "Author not found"
            )

        if "name" in data.model_fields_set and data.name:
            author.name = data.name

        if "biography" in data.model_fields_set:
            author.biography = data.biography

        updated_author = await self.repository.update(
            author
        )

        await self.cache_service.delete_pattern(
            "book:*"
        )

        await self.cache_service.delete_pattern(
            "books:list*"
        )

        return updated_author
