from app.cache.redis_service import CacheService


def disable_cache(monkeypatch):
    async def get(self, key):
        return None

    async def set(self, key, value, expire=300):
        return None

    async def delete(self, key):
        return None

    async def delete_pattern(self, pattern):
        return None

    monkeypatch.setattr(CacheService, "get", get)
    monkeypatch.setattr(CacheService, "set", set)
    monkeypatch.setattr(CacheService, "delete", delete)
    monkeypatch.setattr(CacheService, "delete_pattern", delete_pattern)
