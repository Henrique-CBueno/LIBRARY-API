import json

from app.cache.redis import redis_client


class CacheService:

    async def get(
        self,
        key: str,
    ):
        data = await redis_client.get(key)

        if not data:
            return None

        return json.loads(data)

    async def set(
        self,
        key: str,
        value,
        expire: int = 300,
    ):
        await redis_client.set(
            key,
            json.dumps(value, default=str),
            ex=expire,
        )

    async def delete(
        self,
        key: str,
    ):
        await redis_client.delete(key)