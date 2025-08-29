import redis
from typing import Optional, Any
import json
from app.config import settings


class RedisCache:
    def __init__(self):
        self.redis_client = redis.from_url(settings.redis_url, decode_responses=True)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            value = self.redis_client.get(key)
            if value:
                return json.loads(value)
        except Exception:
            return None
        return None
    
    async def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """Set value in cache with expiration."""
        try:
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, expire, serialized_value)
        except Exception:
            return False
    
    async def delete(self, key: str) -> bool:
        """Delete key from cache."""
        try:
            return bool(self.redis_client.delete(key))
        except Exception:
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """Increment counter in cache."""
        try:
            return self.redis_client.incr(key, amount)
        except Exception:
            return 0
    
    async def set_with_ttl(self, key: str, value: Any, ttl: int) -> bool:
        """Set value with time-to-live."""
        try:
            serialized_value = json.dumps(value, default=str)
            return self.redis_client.setex(key, ttl, serialized_value)
        except Exception:
            return False


# Global cache instance
cache = RedisCache()
