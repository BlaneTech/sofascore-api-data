from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from typing import Optional

from app.db.database import get_db
from app.db.models import Standing, Season, League, Team
from app.schemas import StandingSchema, LeagueBase, SeasonBase, APIResponse

router = APIRouter(prefix="/standings", tags=["Standings"])


@router.get("", response_model=APIResponse)
async def get_standings(
    league_id: int = Query(..., description="ID de la league (requis)"),
    season_id: Optional[int] = Query(None, description="ID de la saison"),
    group: Optional[str] = Query(None, description="Filtrer par groupe"),
    db: AsyncSession = Depends(get_db)
):
    
    # Récupérer la league
    league_query = select(League).where(League.id == league_id)
    league_result = await db.execute(league_query)
    league = league_result.scalar_one_or_none()
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    if not season_id:
        season_query = select(Season).where(
            Season.league_id == league_id,
            Season.current == True
        )
        season_result = await db.execute(season_query)
        season = season_result.scalar_one_or_none()
        
        if not season:
            raise HTTPException(status_code=404, detail="No current season found for this league")
        
        season_id = season.id
    else:
        
        season_query = select(Season).where(Season.id == season_id)
        season_result = await db.execute(season_query)
        season = season_result.scalar_one_or_none()
        
        if not season:
            raise HTTPException(status_code=404, detail="Season not found")
    
    # Récupérer les classements
    query = select(Standing).options(
        joinedload(Standing.team)
    ).where(Standing.season_id == season_id)
    
    if group:
        query = query.where(Standing.group == group)
    
    query = query.order_by(Standing.group, Standing.rank)
    
    result = await db.execute(query)
    standings = result.scalars().all()
    
    # Grouper par groupe
    standings_by_group = {}
    for standing in standings:
        group_name = standing.group or "Overall"
        if group_name not in standings_by_group:
            standings_by_group[group_name] = []
        standings_by_group[group_name].append(
            StandingSchema.model_validate(standing).model_dump()
        )
    
    return APIResponse(
        success=True,
        data={
            "league": LeagueBase.model_validate(league).model_dump(),
            "season": SeasonBase.model_validate(season).model_dump(),
            "standings": standings_by_group
        }
    )


@router.get("/{season_id}/full", response_model=APIResponse)
async def get_full_standings(
    season_id: int,
    db: AsyncSession = Depends(get_db)
):
    
    # Vérifier que la saison existe
    season_query = select(Season).options(
        joinedload(Season.league)
    ).where(Season.id == season_id)
    season_result = await db.execute(season_query)
    season = season_result.scalar_one_or_none()
    
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    
    # Récupérer tous les classements
    query = select(Standing).options(
        joinedload(Standing.team)
    ).where(Standing.season_id == season_id).order_by(Standing.group, Standing.rank)
    
    result = await db.execute(query)
    standings = result.scalars().all()
    
    # Grouper par groupe
    standings_by_group = {}
    for standing in standings:
        group_name = standing.group or "Overall"
        if group_name not in standings_by_group:
            standings_by_group[group_name] = []
        standings_by_group[group_name].append(
            StandingSchema.model_validate(standing).model_dump()
        )
    
    return APIResponse(
        success=True,
        data={
            "league": LeagueBase.model_validate(season.league).model_dump(),
            "season": SeasonBase.model_validate(season).model_dump(),
            "standings": standings_by_group
        }
    )
