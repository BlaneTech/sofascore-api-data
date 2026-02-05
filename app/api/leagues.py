from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional

from app.db.database import get_db
from app.db.models import League, Season
from app.schemas import LeagueBase, SeasonBase, APIResponse, PaginationMeta

router = APIRouter(prefix="/leagues", tags=["Leagues"])


@router.get("", response_model=APIResponse)
async def get_leagues(
    type: Optional[str] = Query(None, description="Type de tournoi (afcon, world_cup, etc.)"),
    country: Optional[str] = Query(None, description="Pays"),
    search: Optional[str] = Query(None, description="Recherche par nom"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    per_page: int = Query(20, ge=1, le=100, description="Résultats par page"),
    db: AsyncSession = Depends(get_db)
):
    
    query = select(League)
    
    if type:
        query = query.where(League.type == type)
    if country:
        query = query.where(League.country.ilike(f"%{country}%"))
    if search:
        query = query.where(League.name.ilike(f"%{search}%"))
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    result = await db.execute(query)
    leagues = result.scalars().all()
    
    # Convertir en schémas
    leagues_data = [LeagueBase.model_validate(league) for league in leagues]
    
    return APIResponse(
        success=True,
        data={"leagues": [league.model_dump() for league in leagues_data]},
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page
        )
    )


@router.get("/{league_id}", response_model=APIResponse)
async def get_league(
    league_id: int,
    db: AsyncSession = Depends(get_db)
):
   
    query = select(League).where(League.id == league_id)
    result = await db.execute(query)
    league = result.scalar_one_or_none()
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    league_data = LeagueBase.model_validate(league)
    
    return APIResponse(
        success=True,
        data={"league": league_data.model_dump()}
    )


@router.get("/{league_id}/seasons", response_model=APIResponse)
async def get_league_seasons(
    league_id: int,
    current: Optional[bool] = Query(None, description="Saison en cours uniquement"),
    db: AsyncSession = Depends(get_db)
):
    
    # Vérifier que la league existe
    league_query = select(League).where(League.id == league_id)
    league_result = await db.execute(league_query)
    league = league_result.scalar_one_or_none()
    
    if not league:
        raise HTTPException(status_code=404, detail="League not found")
    
    # Récupérer les saisons
    query = select(Season).where(Season.league_id == league_id)
    
    if current is not None:
        query = query.where(Season.current == current)
    
    query = query.order_by(Season.year.desc())
    
    result = await db.execute(query)
    seasons = result.scalars().all()
    
    seasons_data = [SeasonBase.model_validate(season) for season in seasons]
    
    return APIResponse(
        success=True,
        data={
            "league": LeagueBase.model_validate(league).model_dump(),
            "seasons": [season.model_dump() for season in seasons_data]
        }
    )
