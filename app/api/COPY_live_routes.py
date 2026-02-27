from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from datetime import datetime, timedelta

from app.db.database import get_db
from app.db.models import Fixture
from app.schemas import APIResponse
from app.services.scraper.live_service import LiveMatchService

router = APIRouter(prefix="/live", tags=["Live Matches"])

live_service = LiveMatchService()


@router.get("/matches", response_model=APIResponse)
async def get_live_matches(db: AsyncSession = Depends(get_db)):
    
    now = datetime.utcnow()
    one_hour_before = now - timedelta(hours=1)
    three_hours_after = now + timedelta(hours=3)
    
    query = select(Fixture).where(
        Fixture.date.between(one_hour_before, three_hours_after)
    )
    result = await db.execute(query)
    fixtures = result.scalars().all()
    
    fixtures_data = []
    for f in fixtures:
        cached = await live_service.get_cached_live_data(f.sofascore_id)
        
        fixtures_data.append({
            "id": f.id,
            "sofascore_id": f.sofascore_id,
            "home_team": f.home_team.name,
            "away_team": f.away_team.name,
            "home_score": f.home_score,
            "away_score": f.away_score,
            "date": f.date.isoformat(),
            "status": cached.get("status") if cached else f.status,
            "kickoff_in_minutes": int((f.date - now).total_seconds() / 60) if f.date > now else None
        })
    
    return APIResponse(success=True, data={"live_matches": fixtures_data})


@router.get("/match/{fixture_id}", response_model=APIResponse)
async def get_live_match_data(
    fixture_id: int,
    db: AsyncSession = Depends(get_db)
):
    
    fixture_query = select(Fixture).where(Fixture.id == fixture_id)
    result = await db.execute(fixture_query)
    fixture = result.scalar_one_or_none()
    
    if not fixture:
        raise HTTPException(status_code=404, detail="Match non trouvé")
    
    now = datetime.utcnow()
    one_hour_before = fixture.date - timedelta(hours=1)
    three_hours_after = fixture.date + timedelta(hours=3)
    
    if not (one_hour_before <= now <= three_hours_after):
        raise HTTPException(
            status_code=400, 
            detail="Match pas dans la fenêtre live (1h avant -> 3h après)"
        )
    
    cached_data = await live_service.get_cached_live_data(fixture.sofascore_id)
    
    if not cached_data:
        cached_data = await live_service.update_live_match(fixture.sofascore_id)
    
    if not cached_data:
        raise HTTPException(status_code=503, detail="Données live indisponibles")
    
    return APIResponse(
        success=True,
        data={
            "fixture": {
                "id": fixture.id,
                "home_team": fixture.home_team.name,
                "away_team": fixture.away_team.name,
                "home_score": fixture.home_score,
                "away_score": fixture.away_score,
                "kickoff": fixture.date.isoformat(),
                "status": cached_data.get("status")
            },
            "live_data": cached_data
        }
    )


@router.get("/match/{fixture_id}/events", response_model=APIResponse)
async def get_live_events(
    fixture_id: int,
    db: AsyncSession = Depends(get_db)
):
    
    fixture_query = select(Fixture).where(Fixture.id == fixture_id)
    result = await db.execute(fixture_query)
    fixture = result.scalar_one_or_none()
    
    if not fixture:
        raise HTTPException(status_code=404, detail="Match non trouvé")
    
    cached_data = await live_service.get_cached_live_data(fixture.sofascore_id)
    
    if not cached_data:
        cached_data = await live_service.update_live_match(fixture.sofascore_id)
    
    events = cached_data.get("incidents", {}) if cached_data else {}
    
    return APIResponse(
        success=True,
        data={
            "fixture_id": fixture.id,
            "timestamp": cached_data.get("timestamp") if cached_data else None,
            "events": events
        }
    )


@router.get("/match/{fixture_id}/stats", response_model=APIResponse)
async def get_live_stats(
    fixture_id: int,
    db: AsyncSession = Depends(get_db)
):
    
    fixture_query = select(Fixture).where(Fixture.id == fixture_id)
    result = await db.execute(fixture_query)
    fixture = result.scalar_one_or_none()
    
    if not fixture:
        raise HTTPException(status_code=404, detail="Match non trouvé")
    
    cached_data = await live_service.get_cached_live_data(fixture.sofascore_id)
    
    if not cached_data:
        cached_data = await live_service.update_live_match(fixture.sofascore_id)
    
    stats = cached_data.get("stats", {}) if cached_data else {}
    
    return APIResponse(
        success=True,
        data={
            "fixture_id": fixture.id,
            "timestamp": cached_data.get("timestamp") if cached_data else None,
            "stats": stats
        }
    )