import json
from redis.asyncio import Redis

from sofascore_wrapper.search import Search
from sofascore_wrapper.player import Player
from sofascore_wrapper.team import Team
from sofascore_wrapper.match import Match

from app.core.settings import settings
from app.services.sofa_client import sofa_client


def _cache_key(prefix: str, value: str) -> str:
    return f"sofa:{prefix}:{value}"


async def cached_get(redis: Redis, key: str):
    raw = await redis.get(key)
    if not raw:
        return None
    try:
        return json.loads(raw)
    except Exception:
        return None


async def cached_set(redis: Redis, key: str, data, ttl: int):
    await redis.set(key, json.dumps(data, ensure_ascii=False), ex=ttl)


async def _ensure_api():
    api = sofa_client.api
    if api is None:
        await sofa_client.start()
        api = sofa_client.api
    if api is None:
        raise RuntimeError("Sofa client not started (start failed)")
    return api


async def search_all(redis: Redis, q: str, sport: str | None):
    key = _cache_key("search", f"{sport or 'any'}:{q}")
    cached = await cached_get(redis, key)
    if cached is not None:
        return cached

    api = await _ensure_api()

    search = Search(api, search_string=q)

    # PyPI example uses search_all() without args.
    try:
        data = await search.search_all()
    except TypeError:
        # fallback for versions that accept sport=
        data = await search.search_all(sport=sport)

    await cached_set(redis, key, data, settings.sofa_cache_ttl)
    return data


async def get_player(redis: Redis, player_id: int):
    key = _cache_key("player", str(player_id))
    cached = await cached_get(redis, key)
    if cached is not None:
        return cached

    api = await _ensure_api()

    player = Player(api, player_id)
    data = await player.get_player()
    await cached_set(redis, key, data, settings.sofa_cache_ttl)
    return data


async def get_team(redis: Redis, team_id: int):
    key = _cache_key("team", str(team_id))
    cached = await cached_get(redis, key)
    if cached is not None:
        return cached

    api = await _ensure_api()

    team = Team(api, team_id)
    data = await team.get_team()
    await cached_set(redis, key, data, settings.sofa_cache_ttl)
    return data


async def get_match(redis: Redis, match_id: int):
    key = _cache_key("match", str(match_id))
    cached = await cached_get(redis, key)
    if cached is not None:
        return cached

    api = await _ensure_api()

    match = Match(api, match_id=match_id)
    data = await match.get_match()
    await cached_set(redis, key, data, settings.sofa_cache_ttl)
    return data
