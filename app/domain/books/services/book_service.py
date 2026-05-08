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
    ):
        self.repository = repository
        self.author_repository = author_repository

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

        return await self.repository.create(
            book
        )

    async def list_books(self):
        return await self.repository.list_books()