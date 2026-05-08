from app.cache.redis_service import CacheService
from app.domain.authors.repositories.author_repository import AuthorRepository
from app.domain.books.models.book_model import BookModel
from app.domain.books.repositories.book_repository import BookRepository
from app.domain.books.schemas.book_schema import CreateBookSchema
from app.exceptions.base import BusinessRuleException, NotFoundException


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

        await self.cache_service.delete(
            "book:list"
        )

        return book_response

    async def list_books(
            self,
            title: str | None = None,
            category: str | None = None,
    ):
        cache_key = (
            f"books:list:{title}:{category}"
        )

        cached_books = (
            await self.cache_service.get(
                cache_key
            )
        )

        if cached_books:
            return cached_books

        books = await self.repository.list_books(
            title,
            category,
        )

        serialized_books = [
            {
                "id": str(book.id),
                "title": book.title,
                "isbn": book.isbn,
                "category": book.category,
                "available_copies": (
                    book.available_copies
                ),
                "author": {
                    "id": str(book.author.id),
                    "name": book.author.name,
                },
            }
            for book in books
        ]

        await self.cache_service.set(
            cache_key,
            serialized_books,
        )

        return serialized_books


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
        }

        await self.cache_service.set(
            cache_key,
            serialized_book,
        )

        return serialized_book