from datetime import datetime

from pydantic import BaseModel


class CreateBookSchema(BaseModel):
    title: str
    isbn: str
    category: str
    total_copies: int
    author_id: str

class AuthorSummarySchema(BaseModel):
    id: str
    name: str

    model_config = {
        "from_attributes": True
    }

class BookResponseSchema(BaseModel):
    id: str
    title: str
    isbn: str
    category: str
    total_copies: int
    available_copies: int
    author: AuthorSummarySchema
    created_at: datetime

    model_config = {
        "from_attributes": True
    }