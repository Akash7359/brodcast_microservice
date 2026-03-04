import time
import redis.asyncio as aioredis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

RATE_LIMITED_PATHS = {"/v1/send-smtp"}


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self.redis: aioredis.Redis | None = None

    async def _get_redis(self) -> aioredis.Redis:
        if self.redis is None:
            self.redis = await aioredis.from_url(settings.REDIS_URL, decode_responses=True)
        return self.redis

    async def dispatch(self, request: Request, call_next):
        if request.url.path not in RATE_LIMITED_PATHS:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        redis = await self._get_redis()
        key = f"rate_limit:{client_ip}"

        try:
            current = await redis.incr(key)
            if current == 1:
                await redis.expire(key, settings.RATE_LIMIT_WINDOW)

            if current > settings.RATE_LIMIT:
                ttl = await redis.ttl(key)
                return JSONResponse(
                    status_code=429,
                    content={
                        "success": False,
                        "message": f"Rate limit exceeded. Try again in {ttl}s.",
                        "retry_after": ttl,
                    },
                )
        except Exception as e:
            logger.warning(f"Rate limit Redis error (allowing request): {e}")

        return await call_next(request)
