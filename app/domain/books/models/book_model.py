import uuid6 as uuid
from datetime import datetime

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from app.infra.database.Base import Base


class BookModel(Base):
    __tablename__ = "books"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid7()),
    )

    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    isbn: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    total_copies: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    available_copies: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    author_id: Mapped[str] = mapped_column(
        String,
        ForeignKey("authors.id"),
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    author = relationship(
        "AuthorModel",
        back_populates="books",
    )