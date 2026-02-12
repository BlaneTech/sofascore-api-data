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
    
    from app.db.models import PlayerStatistics, Season
    
    # Vérifier que le joueur existe
    player_query = select(Player).where(Player.id == player_id)
    player_result = await db.execute(player_query)
    player = player_result.scalar_one_or_none()
    
    season_query = select(Season).where(Season.id == season_id)
    season_result = await db.execute(season_query)
    season = season_result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    query = select(PlayerStatistics).where(PlayerStatistics.player_id == player_id)
    
    if season_id:
        query = query.join(Season).where(Season.id == season_id)
    
    result = await db.execute(query)
    statistics = result.scalar_one_or_none()
    
    if statistics:
        stats_data = {
            "results": {
                "appearances": statistics.appearances,
                "minutes_played": statistics.minutes_played,
                "rating": statistics.rating
            },
            "attack": {
                "goals": statistics.goals,
                "assists": statistics.assists,
                "big_chances_created": statistics.big_chances_created,
                "big_chances_missed": statistics.big_chances_missed,
                "total_shots": statistics.total_shots,
                "shots_on_target": statistics.shots_on_target,
                "shots_off_target": statistics.shots_off_target,
                "shots_inside_box": statistics.shots_from_inside_box,
                "shots_outside_box": statistics.shots_from_outside_box,
                "goal_conversion_percentage": statistics.goal_conversion_percentage,
                "hit_woodwork": statistics.hit_woodwork,
                "own_goals": statistics.own_goals
            },
            "passing": {
                "total_passes": statistics.total_passes,
                "accurate_passes": statistics.accurate_passes,
                "accurate_passes_percentage": statistics.accurate_passes_percentage,
                "key_passes": statistics.key_passes,
                "accurate_crosses": statistics.accurate_crosses,
                "accurate_crosses_percentage": statistics.accurate_crosses_percentage,
                "accurate_long_balls": statistics.accurate_long_balls,
                "accurate_long_balls_percentage": statistics.accurate_long_balls_percentage
            },
            "defense": {
                "tackles": statistics.tackles,
                "tackles_won": statistics.tackles_won,
                "tackles_won_percentage": statistics.tackles_won_percentage,
                "interceptions": statistics.interceptions,
                "clearances": statistics.clearances,
                "successful_dribbles": statistics.successful_dribbles,
                "successful_dribbles_percentage": statistics.successful_dribbles_percentage,
                "dribbled_past": statistics.dribbled_past
            },
            "duels": {
                "total_duels_won": statistics.total_duels_won,
                "total_duels_won_percentage": statistics.total_duels_won_percentage,
                "ground_duels_won": statistics.ground_duels_won,
                "ground_duels_won_percentage": statistics.ground_duels_won_percentage,
                "aerial_duels_won": statistics.aerial_duels_won,
                "aerial_duels_won_percentage": statistics.aerial_duels_won_percentage
            },
            "discipline": {
                "yellow_cards": statistics.yellow_cards,
                "red_cards": statistics.red_cards,
                "fouls": statistics.fouls,
                "was_fouled": statistics.was_fouled,
                "offsides": statistics.offsides
            },
            "goalkeeping": {
                "saves": statistics.saves,
                "clean_sheet": statistics.clean_sheet,
                "goals_conceded": statistics.goals_conceded,
                "penalty_save": statistics.penalty_save
            },
            "set_pieces": {
                "penalty_goals": statistics.penalty_goals,
                "penalties_taken": statistics.penalties_taken,
                "penalty_conversion": statistics.penalty_conversion,
                "touches": statistics.touches,
                "possession_lost": statistics.possession_lost
            }
        }

    else:
        stats_data = None
    
    return APIResponse(
        success=True,
        data={
            "season": PlayerBase.model_validate(season).model_dump(),
            "player": PlayerBase.model_validate(player).model_dump(),
            "statistics": stats_data
        }
    )
