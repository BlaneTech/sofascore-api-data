from fastapi import APIRouter, Request, HTTPException, Depends
from redis.asyncio import Redis

from app.core.settings import settings
from app.core.rate_limit import rate_limit
from app.services.sofa_service import search_all

router = APIRouter(prefix="/admin", tags=["admin"])

async def get_redis(request: Request) -> Redis:
    return request.app.state.redis

def require_key(request: Request):
    key = request.headers.get("X-API-KEY")
    if key != settings.admin_api_key:
        raise HTTPException(status_code=401, detail="unauthorized")

@router.post("/warmup")
async def warmup(q: str = "saka", sport: str | None = "football", request: Request = None, redis: Redis = Depends(get_redis)):
    require_key(request)
    await rate_limit(request, redis)
    data = await search_all(redis, q=q, sport=sport)
    return {"warmed": True, "query": q, "sport": sport, "keys": list((data or {}).keys()) if isinstance(data, dict) else None}
