from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from typing import Optional

from app.db.database import get_db
from app.db.models import Season, League, Fixture, Standing
from app.schemas import SeasonBase, APIResponse, PaginationMeta

router = APIRouter(prefix="/seasons", tags=["Seasons"])


@router.get("", response_model=APIResponse)
async def get_seasons(
    league_id: Optional[int] = Query(None, description="Filtrer par league"),
    current: Optional[bool] = Query(None, description="Saisons en cours uniquement"),
    year: Optional[str] = Query(None, description="Filtrer par année (ex: 2024)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    
    query = select(Season).options(joinedload(Season.league))
    
    if league_id:
        query = query.where(Season.league_id == league_id)
    if current is not None:
        query = query.where(Season.current == current)
    if year:
        query = query.where(Season.year.like(f"%{year}%"))
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    offset = (page - 1) * per_page
    query = query.order_by(Season.year.desc()).offset(offset).limit(per_page)
    
    result = await db.execute(query)
    seasons = result.scalars().all()
    
    seasons_data = [SeasonBase.model_validate(season) for season in seasons]
    
    return APIResponse(
        success=True,
        data={"seasons": [season.model_dump() for season in seasons_data]},
        meta=PaginationMeta(page=page, per_page=per_page, total=total, total_pages=(total + per_page - 1) // per_page)
    )


@router.get("/{season_id}", response_model=APIResponse)
async def get_season(
    season_id: int,
    db: AsyncSession = Depends(get_db)
):
    
    query = select(Season).options(joinedload(Season.league)).where(Season.id == season_id)
    result = await db.execute(query)
    season = result.scalar_one_or_none()
    
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    
    season_data = SeasonBase.model_validate(season)
    
    return APIResponse(
        success=True,
        data={"season": season_data.model_dump()}
    )


@router.get("/{season_id}/fixtures", response_model=APIResponse)
async def get_season_fixtures(
    season_id: int,
    status: Optional[str] = Query(None, description="Filtrer par statut"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    
    from app.schemas import FixtureDetailed
    
    # Vérifier que la saison existe
    season_query = select(Season).where(Season.id == season_id)
    season_result = await db.execute(season_query)
    season = season_result.scalar_one_or_none()
    
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    
    query = select(Fixture).options(
        joinedload(Fixture.home_team),
        joinedload(Fixture.away_team),
        joinedload(Fixture.league),
        joinedload(Fixture.season)
    ).where(Fixture.season_id == season_id)
    
    if status:
        query = query.where(Fixture.status == status)
    
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar()
    
    offset = (page - 1) * per_page
    query = query.order_by(Fixture.date).offset(offset).limit(per_page)
    
    result = await db.execute(query)
    fixtures = result.scalars().all()
    
    fixtures_data = [FixtureDetailed.model_validate(fixture) for fixture in fixtures]
    
    return APIResponse(
        success=True,
        data={
            "season": SeasonBase.model_validate(season).model_dump(),
            "fixtures": [fixture.model_dump() for fixture in fixtures_data]
        },
        meta=PaginationMeta(page=page, per_page=per_page, total=total, total_pages=(total + per_page - 1) // per_page)
    )


@router.get("/{season_id}/standings", response_model=APIResponse)
async def get_season_standings(
    season_id: int,
    group: Optional[str] = Query(None, description="Filtrer par groupe"),
    db: AsyncSession = Depends(get_db)
):
    
    from app.schemas import StandingSchema
    
    # Vérifier que la saison existe
    season_query = select(Season).where(Season.id == season_id)
    season_result = await db.execute(season_query)
    season = season_result.scalar_one_or_none()
    
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    
    query = select(Standing).options(
        joinedload(Standing.team)
    ).where(Standing.season_id == season_id)
    
    if group:
        query = query.where(Standing.group == group)
    
    query = query.order_by(Standing.group, Standing.rank)
    
    result = await db.execute(query)
    standings = result.scalars().all()
    
    standings_data = [StandingSchema.model_validate(standing) for standing in standings]
    
    return APIResponse(
        success=True,
        data={
            "season": SeasonBase.model_validate(season).model_dump(),
            "standings": [standing.model_dump() for standing in standings_data]
        }
    )


@router.get("/{season_id}/statistics", response_model=APIResponse)
async def get_season_statistics(
    season_id: int,
    db: AsyncSession = Depends(get_db)
):
    
    # Vérifier que la saison existe
    season_query = select(Season).where(Season.id == season_id)
    season_result = await db.execute(season_query)
    season = season_result.scalar_one_or_none()
    
    if not season:
        raise HTTPException(status_code=404, detail="Season not found")
    
    # Compter les matchs
    total_matches = (await db.execute(
        select(func.count(Fixture.id)).where(Fixture.season_id == season_id)
    )).scalar()
    
    finished_matches = (await db.execute(
        select(func.count(Fixture.id)).where(
            Fixture.season_id == season_id,
            Fixture.status == 'finished'
        )
    )).scalar()
    
    # Total de buts
    from app.db.models import MatchEvent
    total_goals = (await db.execute(
        select(func.count(MatchEvent.id)).join(
            Fixture, MatchEvent.fixture_id == Fixture.id
        ).where(
            Fixture.season_id == season_id,
            MatchEvent.type == 'goal'
        )
    )).scalar()
    
    # Total de cartons
    total_yellow_cards = (await db.execute(
        select(func.count(MatchEvent.id)).join(
            Fixture, MatchEvent.fixture_id == Fixture.id
        ).where(
            Fixture.season_id == season_id,
            MatchEvent.type == 'yellowCard'
        )
    )).scalar()
    
    total_red_cards = (await db.execute(
        select(func.count(MatchEvent.id)).join(
            Fixture, MatchEvent.fixture_id == Fixture.id
        ).where(
            Fixture.season_id == season_id,
            MatchEvent.type == 'redCard'
        )
    )).scalar()
    
    statistics = {
        "total_matches": total_matches,
        "finished_matches": finished_matches,
        "upcoming_matches": total_matches - finished_matches,
        "total_goals": total_goals,
        "average_goals_per_match": round(total_goals / finished_matches, 2) if finished_matches > 0 else 0,
        "total_yellow_cards": total_yellow_cards,
        "total_red_cards": total_red_cards,
        "total_cards": total_yellow_cards + total_red_cards
    }
    
    return APIResponse(
        success=True,
        data={
            "season": SeasonBase.model_validate(season).model_dump(),
            "statistics": statistics
        }
    )