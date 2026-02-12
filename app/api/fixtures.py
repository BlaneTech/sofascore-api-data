from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import joinedload
from typing import Optional
from datetime import date, datetime

from app.db.database import get_db
from app.db.models import Fixture, Team, League, Season, MatchEvent, Lineup, MatchStatistics
from app.db.models import MatchStatus
from app.schemas import (
    FixtureBase, FixtureDetailed, TeamBase, LeagueBase, SeasonBase,
    MatchEventSchema, LineupSchema, LineupPlayerSchema, PlayerBase,
    MatchStatisticsSchema, APIResponse, PaginationMeta, MatchStatusEnum
)
from app.auth import verify_api_key

router = APIRouter(prefix="/fixtures", tags=["Fixtures"])


@router.get("", response_model=APIResponse)
async def get_fixtures(
    league_id: Optional[int] = Query(None, description="ID de la league"),
    season_id: Optional[int] = Query(None, description="ID de la saison"),
    team_id: Optional[int] = Query(None, description="ID de l'équipe"),
    date: Optional[date] = Query(None, description="Date du match (YYYY-MM-DD)"),
    date_from: Optional[date] = Query(None, description="Date de début"),
    date_to: Optional[date] = Query(None, description="Date de fin"),
    status: Optional[MatchStatus] = Query(None, description="Statut du match"),
    round: Optional[int] = Query(None, description="Numéro du round"),
    live: Optional[bool] = Query(None, description="Matchs en cours uniquement"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    per_page: int = Query(20, ge=1, le=100, description="Résultats par page"),
    # _: None = Depends(verify_api_key),
    db: AsyncSession = Depends(get_db),
    # api_key = Depends(verify_api_key),
):
    
    query = select(Fixture).options(
        joinedload(Fixture.home_team),
        joinedload(Fixture.away_team),
        joinedload(Fixture.league),
        joinedload(Fixture.season)
    )
    
    # Filtres
    if league_id:
        query = query.where(Fixture.league_id == league_id)
    if season_id:
        query = query.where(Fixture.season_id == season_id)
    if team_id:
        query = query.where(
            or_(
                Fixture.home_team_id == team_id,
                Fixture.away_team_id == team_id
            )
        )
    if date:
        # Filtrer par date
        start_of_day = datetime.combine(date, datetime.min.time())
        end_of_day = datetime.combine(date, datetime.max.time())
        query = query.where(
            and_(
                Fixture.date >= start_of_day,
                Fixture.date <= end_of_day
            )
        )
    if date_from:
        query = query.where(Fixture.date >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.where(Fixture.date <= datetime.combine(date_to, datetime.max.time()))
    if status:
        query = query.where(Fixture.status == status)
    if round:
        query = query.where(Fixture.round == round)
    if live:
        query = query.where(Fixture.is_live == live)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    offset = (page - 1) * per_page
    query = query.order_by(Fixture.date.desc()).offset(offset).limit(per_page)
    
    result = await db.execute(query)
    fixtures = result.scalars().all()
    
    # Convertir
    fixtures_data = [FixtureDetailed.model_validate(fixture) for fixture in fixtures]
    
    return APIResponse(
        success=True,
        data={"fixtures": [fixture.model_dump() for fixture in fixtures_data]},
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page
        )
    )


@router.get("/{fixture_id}", response_model=APIResponse)
async def get_fixture(
    fixture_id: int,
    db: AsyncSession = Depends(get_db)
):
    
    query = select(Fixture).options(
        joinedload(Fixture.home_team),
        joinedload(Fixture.away_team),
        joinedload(Fixture.league),
        joinedload(Fixture.season)
    ).where(Fixture.id == fixture_id)
    
    result = await db.execute(query)
    fixture = result.scalar_one_or_none()
    
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    fixture_data = FixtureDetailed.model_validate(fixture)
    
    return APIResponse(
        success=True,
        data={"fixture": fixture_data.model_dump()}
    )


@router.get("/{fixture_id}/events", response_model=APIResponse)
async def get_fixture_events(
    fixture_id: int,
    db: AsyncSession = Depends(get_db)
):
    
    fixture_query = select(Fixture).where(Fixture.id == fixture_id)
    fixture_result = await db.execute(fixture_query)
    fixture = fixture_result.scalar_one_or_none()
    
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # Récupérer les événements
    events_query = select(MatchEvent).options(
        joinedload(MatchEvent.player),
        joinedload(MatchEvent.assist_player)
    ).where(MatchEvent.fixture_id == fixture_id).order_by(MatchEvent.minute)
    
    events_result = await db.execute(events_query)
    events = events_result.scalars().all()
    
    events_data = [MatchEventSchema.model_validate(event) for event in events]
    
    return APIResponse(
        success=True,
        data={
            "fixture_id": fixture_id,
            "events": [event.model_dump() for event in events_data]
        }
    )


@router.get("/{fixture_id}/lineups", response_model=APIResponse)
async def get_fixture_lineups(
    fixture_id: int,
    db: AsyncSession = Depends(get_db)
):
    # Vérifier que le match existe
    fixture_query = select(Fixture).options(
        joinedload(Fixture.home_team),
        joinedload(Fixture.away_team)
    ).where(Fixture.id == fixture_id)
    fixture_result = await db.execute(fixture_query)
    fixture = fixture_result.scalar_one_or_none()
    
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # Récupérer les lineups
    lineups_query = select(Lineup).options(
        joinedload(Lineup.player),
        joinedload(Lineup.team)
    ).where(Lineup.fixture_id == fixture_id)
    
    lineups_result = await db.execute(lineups_query)
    lineups = lineups_result.scalars().all()
    
    # Séparer par équipe
    home_lineups = [l for l in lineups if l.team_id == fixture.home_team_id]
    away_lineups = [l for l in lineups if l.team_id == fixture.away_team_id]
    
    def format_lineup(team, lineup_list):
        starters = []
        substitutes = []
        formation = None
        
        for lineup in lineup_list:
            if not formation and lineup.formation:
                formation = lineup.formation
            
            player_data = LineupPlayerSchema(
                player=PlayerBase.model_validate(lineup.player),
                position=lineup.position,
                formation=lineup.formation,
                starter=lineup.starter,
                substitute=lineup.substitute,
                captain=lineup.captain,
                rating=lineup.rating,
                minutes_played=lineup.minutes_played
            )
            
            if lineup.starter:
                starters.append(player_data)
            else:
                substitutes.append(player_data)
        
        return LineupSchema(
            team=TeamBase.model_validate(team),
            formation=formation,
            starters=starters,
            substitutes=substitutes
        )
    
    home_lineup = format_lineup(fixture.home_team, home_lineups) if home_lineups else None
    away_lineup = format_lineup(fixture.away_team, away_lineups) if away_lineups else None
    
    return APIResponse(
        success=True,
        data={
            "fixture_id": fixture_id,
            "lineups": {
                "home": home_lineup.model_dump() if home_lineup else None,
                "away": away_lineup.model_dump() if away_lineup else None
            }
        }
    )


@router.get("/{fixture_id}/statistics", response_model=APIResponse)
async def get_fixture_statistics(
    fixture_id: int,
    db: AsyncSession = Depends(get_db)
):
    
    # Vérifier que le match existe
    fixture_query = select(Fixture).options(
        joinedload(Fixture.home_team),
        joinedload(Fixture.away_team)
    ).where(Fixture.id == fixture_id)
    fixture_result = await db.execute(fixture_query)
    fixture = fixture_result.scalar_one_or_none()
    
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # Récupérer les statistiques
    stats_query = select(MatchStatistics).options(
        joinedload(MatchStatistics.team)
    ).where(MatchStatistics.fixture_id == fixture_id)
    
    stats_result = await db.execute(stats_query)
    statistics = stats_result.scalars().all()
    
    # Séparer home et away
    home_stats = next((s for s in statistics if s.team_id == fixture.home_team_id), None)
    away_stats = next((s for s in statistics if s.team_id == fixture.away_team_id), None)
    
    return APIResponse(
        success=True,
        data={
            "fixture_id": fixture_id,
            "statistics": {
                "home": MatchStatisticsSchema.model_validate(home_stats).model_dump() if home_stats else None,
                "away": MatchStatisticsSchema.model_validate(away_stats).model_dump() if away_stats else None
            }
        }
    )


# @router.get("/live/all", response_model=APIResponse)
# async def get_live_fixtures(
#     db: AsyncSession = Depends(get_db)
# ):
#     query = select(Fixture).options(
#         joinedload(Fixture.home_team),
#         joinedload(Fixture.away_team),
#         joinedload(Fixture.league),
#         joinedload(Fixture.season)
#     ).where(Fixture.is_live == True).order_by(Fixture.date.desc())
    
#     result = await db.execute(query)
#     fixtures = result.scalars().all()
    
#     fixtures_data = [FixtureDetailed.model_validate(fixture) for fixture in fixtures]
    
#     return APIResponse(
#         success=True,
#         data={
#             "count": len(fixtures_data),
#             "fixtures": [fixture.model_dump() for fixture in fixtures_data]
#         }
#     )
