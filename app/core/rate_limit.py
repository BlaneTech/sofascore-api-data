import time
from fastapi import Request, HTTPException
from redis.asyncio import Redis
from app.core.settings import settings

# Simple Redis token bucket-ish limiter (per IP per minute)
# Key: rl:<ip>:<epoch_minute> -> increment count
async def rate_limit(request: Request, redis: Redis):
    ip = request.client.host if request.client else "unknown"
    minute = int(time.time() // 60)
    key = f"rl:{ip}:{minute}"
    count = await redis.incr(key)
    if count == 1:
        await redis.expire(key, 70)
    if count > settings.rate_limit_per_minute:
        raise HTTPException(status_code=429, detail="rate limit exceeded")
