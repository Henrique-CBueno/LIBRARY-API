from app.config.security.hashing import hash_password
from app.domain.users.models.user_model import UserModel
from app.domain.users.repositories.user_repository import UserRepository
from app.domain.users.schemas.user_schema import CreateUserSchema
from app.exceptions.base import BusinessRuleException, NotFoundException


class UserService:

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def create_user(
        self,
        data: CreateUserSchema,
    ):
        existing_user = await self.repository.find_by_email(
            str(data.email)
        )

        if existing_user:
            raise BusinessRuleException(
                "Email already exists"
            )

        user = UserModel(
            name=data.name,
            email=str(data.email),
            password=hash_password(data.password),
        )

        return await self.repository.create(user)

    async def get_user(
        self,
        user_id: str,
    ):
        user = await self.repository.find_by_id(user_id)

        if not user:
            raise NotFoundException(
                "User not found"
            )

        return user

    async def list_users(self):
        return await self.repository.list_users()