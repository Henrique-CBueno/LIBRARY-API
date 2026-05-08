from datetime import datetime

from pydantic import BaseModel


class CreateBookSchema(BaseModel):
    title: str
    isbn: str
    category: str
    total_copies: int
    author_id: str


class BookResponseSchema(BaseModel):
    id: str
    title: str
    isbn: str
    category: str
    total_copies: int
    available_copies: int
    author_id: str
    created_at: datetime

    model_config = {
        "from_attributes": True
    }