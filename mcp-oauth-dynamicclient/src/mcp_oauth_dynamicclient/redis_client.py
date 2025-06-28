"""Redis client management for OAuth state storage"""

from typing import Optional

import redis.asyncio as redis

from .config import Settings


class RedisManager:
    """Manages Redis connection pool and operations"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self._pool: Optional[redis.Redis] = None

    async def initialize(self):
        """Initialize Redis connection pool"""
        self._pool = redis.from_url(
            self.settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            password=self.settings.redis_password,
        )
        # Test connection
        await self._pool.ping()
        print("✓ Redis connection established")

    async def close(self):
        """Close Redis connection pool"""
        if self._pool:
            await self._pool.close()

    @property
    def client(self) -> redis.Redis:
        """Get Redis client from pool"""
        if not self._pool:
            raise RuntimeError("Redis pool not initialized")
        return self._pool
