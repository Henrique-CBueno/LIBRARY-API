import uuid6 as uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.database.Base import Base


class AuthorModel(Base):
    __tablename__ = "authors"

    id: Mapped[str] = mapped_column(
        String,
        primary_key=True,
        default=lambda: str(uuid.uuid7()),
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    biography: Mapped[str | None] = mapped_column(
        String,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
    )

    books = relationship(
        "BookModel",
        back_populates="author",
    )