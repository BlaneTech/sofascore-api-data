from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional

from app.db.database import get_db
from app.db.models import Player, Team
from app.schemas import PlayerBase, PlayerDetailed, TeamBase, APIResponse, PaginationMeta

router = APIRouter(prefix="/players", tags=["Players"])


@router.get("", response_model=APIResponse)
async def get_players(
    team_id: Optional[int] = Query(None, description="Filtrer par équipe"),
    position: Optional[str] = Query(None, description="Filtrer par position"),
    search: Optional[str] = Query(None, description="Rechercher par nom"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    per_page: int = Query(20, ge=1, le=100, description="Résultats par page"),
    db: AsyncSession = Depends(get_db)
):

    query = select(Player)
    
    # Filtres
    if team_id:
        query = query.where(Player.team_id == team_id)
    if position:
        query = query.where(Player.position == position)
    if search:
        query = query.where(
            or_(
                Player.name.ilike(f"%{search}%"),
                Player.first_name.ilike(f"%{search}%"),
                Player.last_name.ilike(f"%{search}%")
            )
        )
    
    # Compter le total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(Player.name)
    
    result = await db.execute(query)
    players = result.scalars().all()
    
    # Convertir
    players_data = [PlayerBase.model_validate(player) for player in players]
    
    return APIResponse(
        success=True,
        data={"players": [player.model_dump() for player in players_data]},
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page
        )
    )


@router.get("/{player_id}", response_model=APIResponse)
async def get_player(
    player_id: int,
    db: AsyncSession = Depends(get_db)
):

    query = select(Player).where(Player.id == player_id)
    result = await db.execute(query)
    player = result.scalar_one_or_none()
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player_data = PlayerDetailed.model_validate(player)
    
    # Récupérer l'équipe si présente
    team_data = None
    if player.team_id:
        team_query = select(Team).where(Team.id == player.team_id)
        team_result = await db.execute(team_query)
        team = team_result.scalar_one_or_none()
        if team:
            team_data = TeamBase.model_validate(team).model_dump()
    
    return APIResponse(
        success=True,
        data={
            "player": player_data.model_dump(),
            "team": team_data
        }
    )


@router.get("/{player_id}/statistics", response_model=APIResponse)
async def get_player_statistics(
    player_id: int,
    season_id: Optional[int] = Query(None, description="Filtrer par saison"),
    db: AsyncSession = Depends(get_db)
):
    
    from app.db.models import PlayerStatistics, Fixture
    
    # Vérifier que le joueur existe
    player_query = select(Player).where(Player.id == player_id)
    player_result = await db.execute(player_query)
    player = player_result.scalar_one_or_none()
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    query = select(PlayerStatistics).where(PlayerStatistics.player_id == player_id)
    
    if season_id:
        query = query.join(Fixture).where(Fixture.season_id == season_id)
    
    result = await db.execute(query)
    statistics = result.scalars().all()
    
    # Agréger les statistiques
    if statistics:
        total_stats = {
            "matches_played": len(statistics),
            "goals": sum(s.goals or 0 for s in statistics),
            "assists": sum(s.assists or 0 for s in statistics),
            "shots": sum(s.shots or 0 for s in statistics),
            "shots_on_target": sum(s.shots_on_target or 0 for s in statistics),
            "passes": sum(s.passes or 0 for s in statistics),
            "tackles": sum(s.tackles or 0 for s in statistics),
            "interceptions": sum(s.interceptions or 0 for s in statistics),
            "fouls": sum(s.fouls or 0 for s in statistics),
            "yellow_cards": sum(s.yellow_cards or 0 for s in statistics),
            "red_cards": sum(s.red_cards or 0 for s in statistics),
            "minutes_played": sum(s.minutes_played or 0 for s in statistics),
            "average_rating": sum(s.rating or 0 for s in statistics if s.rating) / len([s for s in statistics if s.rating]) if any(s.rating for s in statistics) else None
        }
    else:
        total_stats = None
    
    return APIResponse(
        success=True,
        data={
            "player": PlayerBase.model_validate(player).model_dump(),
            "statistics": total_stats
        }
    )
