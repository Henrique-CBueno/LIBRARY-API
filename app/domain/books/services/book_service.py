from app.cache.redis_service import CacheService
from app.domain.authors.repositories.author_repository import AuthorRepository
from app.domain.books.models.book_model import BookModel
from app.domain.books.repositories.book_repository import BookRepository
from app.domain.books.schemas.book_schema import CreateBookSchema, UpdateBookSchema
from app.exceptions.base import BusinessRuleException, NotFoundException
from app.infra.middleware.logging import logger


class BookService:

    def __init__(
        self,
        repository: BookRepository,
        author_repository: AuthorRepository,
        cache_service: CacheService,
    ):
        self.repository = repository
        self.author_repository = author_repository
        self.cache_service = cache_service

    async def create_book(
        self,
        data: CreateBookSchema,
    ):
        existing_book = (
            await self.repository.find_by_isbn(
                data.isbn
            )
        )

        if existing_book:
            raise BusinessRuleException(
                "ISBN already exists"
            )

        author = (
            await self.author_repository.find_by_id(
                data.author_id
            )
        )

        if not author:
            raise NotFoundException(
                "Author not found"
            )

        book = BookModel(
            title=data.title,
            isbn=data.isbn,
            category=data.category,
            total_copies=data.total_copies,
            available_copies=data.total_copies,
            author_id=data.author_id,
        )

        book_response = await self.repository.create(
            book
        )

        await self.cache_service.delete_pattern(
            "books:list*"
        )

        return {
            "id": str(book_response.id),
            "title": book_response.title,
            "isbn": book_response.isbn,
            "category": book_response.category,
            "total_copies": book_response.total_copies,
            "available_copies": book_response.available_copies,
            "author": {
                "id": str(author.id),
                "name": author.name,
            },
            "created_at": book_response.created_at,
        }

    async def list_books_paginated(
            self,
            page: int,
            size: int,
            title: str | None = None,
            category: str | None = None,
            author: str | None = None,
            available: bool | None = None,
    ):
        cache_key = (
            f"books:list:{page}:{size}:{title}:{category}:{author}:{available}"
        )

        cached_books = await self.cache_service.get(
            cache_key
        )

        if cached_books:
            return cached_books

        books, total = (
            await self.repository.list_books_paginated(
                page,
                size,
                title,
                category,
                author,
                available,
            )
        )

        serialized_books = [
            {
                "id": str(book.id),
                "title": book.title,
                "isbn": book.isbn,
                "category": book.category,
                "total_copies": book.total_copies,
                "available_copies": (
                    book.available_copies
                ),
                "author": {
                    "id": str(book.author.id),
                    "name": book.author.name,
                },
                "created_at": book.created_at,
            }
            for book in books
        ]

        response = {
            "items": serialized_books,
            "total": total,
            "page": page,
            "size": size,
        }

        await self.cache_service.set(
            cache_key,
            response,
        )

        return response


    async def get_book(
            self,
            book_id,
    ):
        cache_key = f"book:{book_id}"

        cached_book = await self.cache_service.get(
            cache_key
        )

        if cached_book:
            return cached_book

        book = await self.repository.find_by_id(
            book_id
        )

        if not book:
            raise NotFoundException(
                "Book not found"
            )

        serialized_book = {
            "id": str(book.id),
            "title": book.title,
            "isbn": book.isbn,
            "category": book.category,
            "total_copies": book.total_copies,
            "available_copies": book.available_copies,
            "author": {
                "id": str(book.author.id),
                "name": book.author.name,
            },
            "created_at": book.created_at,
        }

        await self.cache_service.set(
            cache_key,
            serialized_book,
        )

        return serialized_book

    async def update_book(
            self,
            book_id,
            data: UpdateBookSchema,
    ):
        book = await self.repository.find_by_id(
            book_id
        )

        if not book:
            raise NotFoundException(
                "Book not found"
            )

        borrowed_books = (
                book.total_copies
                - book.available_copies
        )

        if (
                data.total_copies is not None
                and data.total_copies < borrowed_books
        ):
            raise BusinessRuleException(
                "total_copies cannot be lower than borrowed books"
            )

        if data.title:
            book.title = data.title

        if data.category:
            book.category = data.category

        if data.total_copies is not None:
            difference = (
                    data.total_copies
                    - book.total_copies
            )

            book.total_copies = (
                data.total_copies
            )

            book.available_copies += (
                difference
            )

        updated_book = (
            await self.repository.update(book)
        )

        await self.cache_service.delete(
            f"book:{book_id}"
        )

        await self.cache_service.delete_pattern(
            "books:list*"
        )

        logger.info(
            "book_updated",
            book_id=str(book.id),
        )

        return updated_book

    async def delete_book(
            self,
            book_id,
    ):
        book = await self.repository.find_by_id(
            book_id
        )

        if not book:
            raise NotFoundException(
                "Book not found"
            )

        await self.repository.soft_delete(book)

        await self.cache_service.delete(
            f"book:{book_id}"
        )

        await self.cache_service.delete_pattern(
            "books:list*"
        )

        logger.info(
            "book_deleted",
            book_id=str(book.id),
        )
