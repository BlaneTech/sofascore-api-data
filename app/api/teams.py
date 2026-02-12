from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from typing import Optional

from app.db.database import get_db
from app.db.models import Team, Player,TeamStatistics, Season
from app.schemas import TeamBase, TeamDetailed, PlayerBase, APIResponse, PaginationMeta, SeasonBase


router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("", response_model=APIResponse)
async def get_teams(
    country: Optional[str] = Query(None, description="Filtrer par pays"),
    national: Optional[bool] = Query(None, description="Équipes nationales uniquement"),
    search: Optional[str] = Query(None, description="Rechercher par nom"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    per_page: int = Query(20, ge=1, le=100, description="Résultats par page"),
    db: AsyncSession = Depends(get_db)
):
    # Construire la requête
    query = select(Team)
    
    # Filtres
    if country:
        query = query.where(Team.country.ilike(f"%{country}%"))
    if national is not None:
        query = query.where(Team.national == national)
    if search:
        query = query.where(
            or_(
                Team.name.ilike(f"%{search}%"),
                Team.short_name.ilike(f"%{search}%"),
                Team.code.ilike(f"%{search}%")
            )
        )
    
    # Compter le total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Pagination
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(Team.name)
    
    result = await db.execute(query)
    teams = result.scalars().all()
    
    # Convertir
    teams_data = [TeamBase.model_validate(team) for team in teams]
    
    return APIResponse(
        success=True,
        data={"teams": [team.model_dump() for team in teams_data]},
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page
        )
    )


@router.get("/{team_id}", response_model=APIResponse)
async def get_team(
    team_id: int,
    db: AsyncSession = Depends(get_db)
):
    
    query = select(Team).where(Team.id == team_id)
    result = await db.execute(query)
    team = result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    team_data = TeamDetailed.model_validate(team)
    
    return APIResponse(
        success=True,
        data={"team": team_data.model_dump()}
    )


@router.get("/{team_id}/players", response_model=APIResponse)
async def get_team_players(
    team_id: int,
    position: Optional[str] = Query(None, description="Filtrer par position"),
    db: AsyncSession = Depends(get_db)
):
    
    # Vérifier que l'équipe existe
    team_query = select(Team).where(Team.id == team_id)
    team_result = await db.execute(team_query)
    team = team_result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Récupérer les joueurs
    query = select(Player).where(Player.team_id == team_id)
    
    if position:
        query = query.where(Player.position == position)
    
    query = query.order_by(Player.jersey_number)
    
    result = await db.execute(query)
    players = result.scalars().all()
    
    players_data = [PlayerBase.model_validate(player) for player in players]
    
    return APIResponse(
        success=True,
        data={
            "team": TeamBase.model_validate(team).model_dump(),
            "players": [player.model_dump() for player in players_data]
        }
    )


@router.get("/{team_id}/season/{season_id}/statistics", response_model=APIResponse)
async def get_team_statistics(
    team_id: int,
    season_id: int,
    db: AsyncSession = Depends(get_db)
):
    
    # Vérifier que l'équipe existe
    team_query = select(Team).where(Team.id == team_id)
    team_result = await db.execute(team_query)
    team = team_result.scalar_one_or_none()
    
    season_query = select(Season).where(Season.id == season_id)
    season_result = await db.execute(season_query)
    season = season_result.scalar_one_or_none()

    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Récupérer les statistiques
    stats_query = select(TeamStatistics).where(TeamStatistics.team_id == team_id)

    if season_id:
        stats_query = stats_query.join(Season).where(Season.id == season_id)

    stats_result = await db.execute(stats_query)
    stats = stats_result.scalar_one_or_none()
    
    stats_data = None
    if stats:
        stats_data = {
            "results": {
                "matches": stats.matches,
                "wins": stats.wins,
                "draws": stats.draws,
                "losses": stats.losses,
                "points": getattr(stats, "points", None)
            },
            "attack": {
                "goals_scored": stats.goals_scored,
                "goals_conceded": stats.goals_conceded,
                "goal_difference": stats.goals_scored - stats.goals_conceded,
                "assists": stats.assists,
                "shots": stats.shots,
                "shots_on_target": stats.shots_on_target,
                "shots_off_target": stats.shots_off_target,
                "shots_inside_box": stats.shots_from_inside_box,
                "shots_outside_box": stats.shots_from_outside_box,
                "big_chances": stats.big_chances,
                "big_chances_created": stats.big_chances_created,
                "big_chances_missed": stats.big_chances_missed,
                "hit_woodwork": stats.hit_woodwork,
                "successful_dribbles": stats.successful_dribbles,
                "dribble_attempts": stats.dribble_attempts
            },
            "passing": {
                "total_passes": stats.total_passes,
                "accurate_passes": stats.accurate_passes,
                "accuracy_percentage": stats.accurate_passes_percentage,
                "total_long_balls": stats.total_long_balls,
                "accurate_long_balls": stats.accurate_long_balls,
                "long_ball_accuracy": stats.accurate_long_balls_percentage,
                "total_crosses": stats.total_crosses,
                "accurate_crosses": stats.accurate_crosses,
                "cross_accuracy": stats.accurate_crosses_percentage,
                "average_possession": stats.average_ball_possession
            },
            "defense": {
                "tackles": stats.tackles,
                "interceptions": stats.interceptions,
                "clearances": stats.clearances,
                "saves": stats.saves,
                "clean_sheets": stats.clean_sheets,
                "blocked_shots": stats.blocked_scoring_attempt,
                "ball_recovery": stats.ball_recovery,
                "errors_leading_to_goal": stats.errors_leading_to_goal
            },
            "duels": {
                "total_duels": stats.total_duels,
                "duels_won": stats.duels_won,
                "duels_won_percentage": stats.duels_won_percentage,
                "ground_duels_won": stats.ground_duels_won,
                "ground_duels_won_percentage": stats.ground_duels_won_percentage,
                "aerial_duels_won": stats.aerial_duels_won,
                "aerial_duels_won_percentage": stats.aerial_duels_won_percentage
            },
            "discipline": {
                "yellow_cards": stats.yellow_cards,
                "red_cards": stats.red_cards,
                "fouls": stats.fouls,
                "offsides": stats.offsides,
                "corners": stats.corners,
                "free_kicks": stats.free_kicks,
                "penalties_taken": stats.penalties_taken,
                "penalty_goals": stats.penalty_goals,
                "penalties_committed": stats.penalties_commited
            }
        }


    
    return APIResponse(
        success=True,
        data={
            "season": SeasonBase.model_validate(season).model_dump(),
            "team": TeamBase.model_validate(team).model_dump(),
            "statistics": stats_data
        }
    )
