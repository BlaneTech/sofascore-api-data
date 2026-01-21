from fastapi import APIRouter, Depends, Request, HTTPException
from redis.asyncio import Redis

from app.core.rate_limit import rate_limit
from app.core.settings import settings
from app.services.sofa_service import search_all, get_player, get_team, get_match
from app.db.session import SessionLocal
from app.db.models import Entity
from app.schemas.common import StoreResult

router = APIRouter()

async def get_redis(request: Request) -> Redis:
    # Fallback safe: if startup didn't set app.state.redis, create it here.
    r = getattr(request.app.state, "redis", None)
    if r is None:
        r = Redis.from_url(settings.redis_url, decode_responses=True)
        request.app.state.redis = r
    return r

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.get("/sofa/search")
async def sofa_search(q: str, sport: str | None = None, request: Request = None, redis: Redis = Depends(get_redis)):
    await rate_limit(request, redis)
    return await search_all(redis, q=q, sport=sport)

@router.get("/sofa/player/{player_id}")
async def sofa_player(player_id: int, request: Request = None, redis: Redis = Depends(get_redis)):
    await rate_limit(request, redis)
    return await get_player(redis, player_id)

@router.get("/sofa/team/{team_id}")
async def sofa_team(team_id: int, request: Request = None, redis: Redis = Depends(get_redis)):
    await rate_limit(request, redis)
    return await get_team(redis, team_id)

@router.get("/sofa/match/{match_id}")
async def sofa_match(match_id: int, request: Request = None, redis: Redis = Depends(get_redis)):
    await rate_limit(request, redis)
    return await get_match(redis, match_id)

# ---- Optional persistence (JSONB) ----
@router.post("/store/player/{player_id}", response_model=StoreResult)
async def store_player(player_id: int, request: Request = None, redis: Redis = Depends(get_redis)):
    await rate_limit(request, redis)
    payload = await get_player(redis, player_id)

    async with SessionLocal() as db:
        row = Entity(kind="player", external_id=str(player_id), payload=payload)
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return StoreResult(stored=True, id=row.id)

@router.post("/store/team/{team_id}", response_model=StoreResult)
async def store_team(team_id: int, request: Request = None, redis: Redis = Depends(get_redis)):
    await rate_limit(request, redis)
    payload = await get_team(redis, team_id)

    async with SessionLocal() as db:
        row = Entity(kind="team", external_id=str(team_id), payload=payload)
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return StoreResult(stored=True, id=row.id)

@router.post("/store/match/{match_id}", response_model=StoreResult)
async def store_match(match_id: int, request: Request = None, redis: Redis = Depends(get_redis)):
    await rate_limit(request, redis)
    payload = await get_match(redis, match_id)

    async with SessionLocal() as db:
        row = Entity(kind="match", external_id=str(match_id), payload=payload)
        db.add(row)
        await db.commit()
        await db.refresh(row)
        return StoreResult(stored=True, id=row.id)
