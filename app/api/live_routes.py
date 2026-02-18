from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.models import Fixture
from app.schemas import APIResponse
from app.services.scraper.live_service import LiveMatchService

router = APIRouter(prefix="/live", tags=["Live Matches"])

live_service = LiveMatchService()


async def _get_cached_or_fetch(sofascore_id: int) -> dict:
    cached = await live_service.get_cached_live_data(sofascore_id)
    if not cached:
        cached = await live_service.update_live_match(sofascore_id)
    if not cached:
        raise HTTPException(status_code=503, detail="Données live indisponibles")
    return cached

@router.get("/matches", response_model=APIResponse)
async def get_live_matches(db: AsyncSession = Depends(get_db)):
    
    now = datetime.utcnow()
    one_hour_before = now - timedelta(hours=1)
    three_hours_after = now + timedelta(hours=3)

    # DB
    query = select(Fixture).where(Fixture.date.between(one_hour_before, three_hours_after))
    result = await db.execute(query)
    db_fixtures = result.scalars().all()
    fixtures_map = {f.sofascore_id: f for f in db_fixtures}

    # IDs live (DB + Sofascore)
    live_sofascore_ids = await live_service.get_live_fixtures(db)

    matches = []

    # Matchs DB — infos enrichies depuis le cache
    for sofascore_id, fixture in fixtures_map.items():
        cached = await live_service.get_cached_live_data(sofascore_id)
        match_info = cached.get("match_info", {}) if cached else {}
        score = match_info.get("score", {})

        matches.append({
            "sofascore_id": sofascore_id,
            "db_id": fixture.id,
            "source": "db",
            "tournament": match_info.get("tournament") or fixture.league.name if fixture.league else None,
            "home_team": match_info.get("home_team", {}).get("name") or fixture.home_team.name,
            "away_team": match_info.get("away_team", {}).get("name") or fixture.away_team.name,
            "score": {
                "home": score.get("home", fixture.home_score),
                "away": score.get("away", fixture.away_score),
            },
            "minute": match_info.get("minute"),
            "status": cached.get("status") if cached else fixture.status,
            "status_description": match_info.get("status_description"),
            "kickoff": fixture.date.isoformat(),
            "kickoff_in_minutes": int((fixture.date - now).total_seconds() / 60) if fixture.date > now else None,
        })

    # Matchs Sofascore absents de la DB
    for sofascore_id in live_sofascore_ids:
        if sofascore_id in fixtures_map:
            continue
        cached = await live_service.get_cached_live_data(sofascore_id)
        if not cached:
            cached = await live_service.update_live_match(sofascore_id)
        if not cached:
            continue

        match_info = cached.get("match_info", {})
        score = match_info.get("score", {})

        matches.append({
            "sofascore_id": sofascore_id,
            "db_id": None,
            "source": "sofascore_live",
            "tournament": match_info.get("tournament"),
            "home_team": match_info.get("home_team", {}).get("name"),
            "away_team": match_info.get("away_team", {}).get("name"),
            "score": {
                "home": score.get("home"),
                "away": score.get("away"),
            },
            "minute": match_info.get("minute"),
            "status": cached.get("status"),
            "status_description": match_info.get("status_description"),
            "kickoff": None,
            "kickoff_in_minutes": None,
        })

    return APIResponse(success=True, data={"matches": matches, "total": len(matches)})


@router.get("/match/{sofascore_id}", response_model=APIResponse)
async def get_live_match(sofascore_id: int, db: AsyncSession = Depends(get_db)):
    
    fixture_query = select(Fixture).where(Fixture.sofascore_id == sofascore_id)
    result = await db.execute(fixture_query)
    fixture = result.scalar_one_or_none()

    cached = await _get_cached_or_fetch(sofascore_id)
    match_info = cached.get("match_info", {})
    score = match_info.get("score", {})

    # Score par période depuis les incidents (periods)
    incidents = cached.get("incidents") or {}
    periods = incidents.get("periods", [])
    ht_score = next((p for p in periods if p.get("text") == "HT"), None)

    return APIResponse(success=True, data={
        "sofascore_id": sofascore_id,
        "in_db": fixture is not None,
        "status": cached.get("status"),
        "status_description": match_info.get("status_description"),
        "minute": match_info.get("minute"),
        "tournament": match_info.get("tournament"),
        "kickoff": fixture.date.isoformat() if fixture else None,
        "home_team": match_info.get("home_team"),
        "away_team": match_info.get("away_team"),
        "score": {
            "current": {
                "home": score.get("home"),
                "away": score.get("away"),
            },
            "half_time": {
                "home": ht_score.get("home_score") if ht_score else score.get("home_period1"),
                "away": ht_score.get("away_score") if ht_score else score.get("away_period1"),
            },
            "period1": {
                "home": score.get("home_period1"),
                "away": score.get("away_period1"),
            },
            "period2": {
                "home": score.get("home_period2"),
                "away": score.get("away_period2"),
            },
        },
        "last_updated": cached.get("timestamp"),
    })

@router.get("/match/{sofascore_id}/events", response_model=APIResponse)
async def get_live_events(sofascore_id: int, db: AsyncSession = Depends(get_db)):
    
    cached = await _get_cached_or_fetch(sofascore_id)
    incidents = cached.get("incidents") or {}
    events = incidents.get("events", [])
    periods = incidents.get("periods", [])

    goals        = [e for e in events if e["type"] == "goal"]
    cards        = [e for e in events if e["type"] == "card"]
    substitutions = [e for e in events if e["type"] == "substitution"]
    var_decisions = [e for e in events if e["type"] == "var"]
    injury_times  = [e for e in events if e["type"] == "injury_time"]

    return APIResponse(success=True, data={
        "sofascore_id": sofascore_id,
        "status": cached.get("status"),
        "last_updated": cached.get("timestamp"),
        "timeline": events,
        "by_type": {
            "goals": goals,
            "cards": cards,
            "substitutions": substitutions,
            "var": var_decisions,
            "injury_time": injury_times,
        },
        "periods": periods,
        "totals": {
            "goals": len(goals),
            "yellow_cards": len([c for c in cards if c.get("card_type") == "yellow"]),
            "red_cards": len([c for c in cards if c.get("card_type") in ["red", "yellowRed"]]),
            "substitutions": len(substitutions),
        }
    })

@router.get("/match/{sofascore_id}/stats", response_model=APIResponse)
async def get_live_stats(sofascore_id: int, db: AsyncSession = Depends(get_db)):
    
    cached = await _get_cached_or_fetch(sofascore_id)
    stats = cached.get("stats")
    match_info = cached.get("match_info", {})

    # Extraire les stats
    summary = {}
    if stats and "all" in stats:
        overview = stats["all"].get("match_overview", {})
        summary = {
            "possession": {
                "home": overview.get("ballPossession", {}).get("home_display"),
                "away": overview.get("ballPossession", {}).get("away_display"),
            },
            "shots": {
                "home": overview.get("totalShotsOnGoal", {}).get("home"),
                "away": overview.get("totalShotsOnGoal", {}).get("away"),
            },
            "corners": {
                "home": overview.get("cornerKicks", {}).get("home"),
                "away": overview.get("cornerKicks", {}).get("away"),
            },
            "yellow_cards": {
                "home": overview.get("yellowCards", {}).get("home"),
                "away": overview.get("yellowCards", {}).get("away"),
            },
        }

    return APIResponse(success=True, data={
        "sofascore_id": sofascore_id,
        "status": cached.get("status"),
        "last_updated": cached.get("timestamp"),
        "home_team": match_info.get("home_team", {}).get("name"),
        "away_team": match_info.get("away_team", {}).get("name"),
        "available": stats is not None,   
        "summary": summary,        
        "details": stats,            
    })

@router.get("/match/{sofascore_id}/lineups", response_model=APIResponse)
async def get_live_lineups(sofascore_id: int, db: AsyncSession = Depends(get_db)):
   
    cached = await _get_cached_or_fetch(sofascore_id)
    lineups = cached.get("lineups")
    match_info = cached.get("match_info", {})

    return APIResponse(success=True, data={
        "sofascore_id": sofascore_id,
        "status": cached.get("status"),
        "last_updated": cached.get("timestamp"),
        "home_team": match_info.get("home_team", {}).get("name"),
        "away_team": match_info.get("away_team", {}).get("name"),
        "available": lineups is not None,
        "lineups": lineups,
    })