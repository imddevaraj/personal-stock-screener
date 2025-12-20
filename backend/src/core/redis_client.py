"""Redis client configuration and utilities."""
import redis
from typing import Optional
from .config import settings
from .logging import get_logger

logger = get_logger(__name__)


class RedisClient:
    """Redis client wrapper with connection pooling."""
    
    def __init__(self):
        """Initialize Redis client."""
        self._client: Optional[redis.Redis] = None
        self._pool: Optional[redis.ConnectionPool] = None
    
    def connect(self) -> redis.Redis:
        """
        Get or create Redis connection.
        
        Returns:
            Redis client instance
        """
        if self._client is None:
            self._pool = redis.ConnectionPool.from_url(
                settings.REDIS_URL,
                max_connections=20,
                decode_responses=True
            )
            self._client = redis.Redis(connection_pool=self._pool)
            logger.info("Redis connection established")
        return self._client
    
    def close(self) -> None:
        """Close Redis connection."""
        if self._client:
            self._client.close()
            self._client = None
        if self._pool:
            self._pool.disconnect()
            self._pool = None
            logger.info("Redis connection closed")
    
    def check_connection(self) -> bool:
        """
        Check if Redis connection is working.
        
        Returns:
            True if connection is successful, False otherwise
        """
        try:
            client = self.connect()
            client.ping()
            logger.info("Redis connection successful")
            return True
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            return False


# Global Redis client instance
redis_client = RedisClient()


def get_redis() -> redis.Redis:
    """
    Get Redis client instance.
    
    Returns:
        Redis client
    """
    return redis_client.connect()
