from datetime import datetime

from pydantic import BaseModel


class CreateAuthorSchema(BaseModel):
    name: str
    biography: str | None = None


class AuthorResponseSchema(BaseModel):
    id: str
    name: str
    biography: str | None
    created_at: datetime

    model_config = {
        "from_attributes": True
    }