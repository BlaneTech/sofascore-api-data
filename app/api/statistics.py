from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import joinedload
from sqlalchemy import case
from typing import Optional
from app.db.models import Standing

from app.db.database import get_db
from app.db.models import (
    MatchStatistics, PlayerStatistics, TeamStatistics,
    Fixture, Player, Team, Season
)
from app.schemas import APIResponse

router = APIRouter(prefix="/statistics", tags=["Statistics"])


@router.get("/match/{fixture_id}", response_model=APIResponse)
async def get_match_statistics_detailed(
    fixture_id: int,
    db: AsyncSession = Depends(get_db)
):
    
    # Récupérer le match
    fixture_query = select(Fixture).options(
        joinedload(Fixture.home_team),
        joinedload(Fixture.away_team)
    ).where(Fixture.id == fixture_id)
    
    fixture_result = await db.execute(fixture_query)
    fixture = fixture_result.scalar_one_or_none()
    
    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")
    
    # Récupérer les stats
    stats_query = select(MatchStatistics).options(
        joinedload(MatchStatistics.team)
    ).where(MatchStatistics.fixture_id == fixture_id)
    
    stats_result = await db.execute(stats_query)
    statistics = stats_result.scalars().all()
    
    home_stats = next((s for s in statistics if s.team_id == fixture.home_team_id), None)
    away_stats = next((s for s in statistics if s.team_id == fixture.away_team_id), None)
    
    # Créer des comparaisons
    comparisons = {}
    if home_stats and away_stats:
        comparisons = {
            "possession": {
                "home": home_stats.ball_possession,
                "away": away_stats.ball_possession,
                "winner": "home" if (home_stats.ball_possession or 0) > (away_stats.ball_possession or 0) else "away"
            },
            "shots": {
                "home": home_stats.total_shots,
                "away": away_stats.total_shots,
                "winner": "home" if (home_stats.total_shots or 0) > (away_stats.total_shots or 0) else "away"
            },
            "shots_on_target": {
                "home": home_stats.shots_on_goal,
                "away": away_stats.shots_on_goal,
                "winner": "home" if (home_stats.shots_on_goal or 0) > (away_stats.shots_on_goal or 0) else "away"
            },
            "passes": {
                "home": home_stats.passes,
                "away": away_stats.passes,
                "winner": "home" if (home_stats.passes or 0) > (away_stats.passes or 0) else "away"
            },
            "pass_accuracy": {
                "home": home_stats.pass_accuracy,
                "away": away_stats.pass_accuracy,
                "winner": "home" if (home_stats.pass_accuracy or 0) > (away_stats.pass_accuracy or 0) else "away"
            }
        }
    
    return APIResponse(
        success=True,
        data={
            "fixture": {
                "id": fixture.id,
                "home_team": fixture.home_team.name,
                "away_team": fixture.away_team.name,
                "score": f"{fixture.home_score or 0} - {fixture.away_score or 0}"
            },
            "statistics": {
                "home": {
                    "team": fixture.home_team.name,
                    "possession": home_stats.ball_possession if home_stats else None,
                    "shots": home_stats.total_shots if home_stats else None,
                    "shots_on_target": home_stats.shots_on_goal if home_stats else None,
                    "passes": home_stats.passes if home_stats else None,
                    "pass_accuracy": home_stats.pass_accuracy if home_stats else None,
                    "corners": home_stats.corners if home_stats else None,
                    "fouls": home_stats.fouls if home_stats else None,
                    "offsides": home_stats.offsides if home_stats else None,
                    "yellow_cards": home_stats.yellow_cards if home_stats else None,
                    "red_cards": home_stats.red_cards if home_stats else None,
                } if home_stats else None,
                "away": {
                    "team": fixture.away_team.name,
                    "possession": away_stats.ball_possession if away_stats else None,
                    "shots": away_stats.total_shots if away_stats else None,
                    "shots_on_target": away_stats.shots_on_goal if away_stats else None,
                    "passes": away_stats.passes if away_stats else None,
                    "pass_accuracy": away_stats.pass_accuracy if away_stats else None,
                    "corners": away_stats.corners if away_stats else None,
                    "fouls": away_stats.fouls if away_stats else None,
                    "offsides": away_stats.offsides if away_stats else None,
                    "yellow_cards": away_stats.yellow_cards if away_stats else None,
                    "red_cards": away_stats.red_cards if away_stats else None,
                } if away_stats else None
            },
            "comparisons": comparisons
        }
    )


@router.get("/player/{player_id}/season/{season_id}", response_model=APIResponse)
async def get_player_season_statistics(
    player_id: int,
    season_id: int,
    db: AsyncSession = Depends(get_db)
):

    # Vérifier que le joueur existe
    player_query = select(Player).where(Player.id == player_id)
    player_result = await db.execute(player_query)
    player = player_result.scalar_one_or_none()
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    # Récupérer toutes les stats du joueur pour la saison
    stats_query = select(PlayerStatistics).join(
        Fixture, PlayerStatistics.fixture_id == Fixture.id
    ).where(
        PlayerStatistics.player_id == player_id,
        Fixture.season_id == season_id
    )
    
    result = await db.execute(stats_query)
    statistics = result.scalars().all()
    
    if not statistics:
        return APIResponse(
            success=True,
            data={
                "player": {
                    "id": player.id,
                    "name": player.name,
                    "position": player.position
                },
                "season_id": season_id,
                "statistics": None,
                "message": "No statistics for this season"
            }
        )
    
    # Agréger les statistiques
    aggregated = {
        "matches_played": len(statistics),
        "minutes_played": sum(s.minutes_played or 0 for s in statistics),
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
        "dribbles": sum(s.dribbles or 0 for s in statistics),
        "average_rating": round(
            sum(s.rating or 0 for s in statistics if s.rating) / 
            len([s for s in statistics if s.rating]), 2
        ) if any(s.rating for s in statistics) else None
    }
    
    return APIResponse(
        success=True,
        data={
            "player": {
                "id": player.id,
                "name": player.name,
                "position": player.position,
                "jersey_number": player.jersey_number
            },
            "season_id": season_id,
            "statistics": aggregated
        }
    )


@router.get("/team/{team_id}/season/{season_id}", response_model=APIResponse)
async def get_team_season_statistics(
    team_id: int,
    season_id: int,
    db: AsyncSession = Depends(get_db)
):

    # Vérifier que l'équipe existe
    team_query = select(Team).where(Team.id == team_id)
    team_result = await db.execute(team_query)
    team = team_result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    # Récupérer tous les matchs de l'équipe pour la saison
    fixtures_query = select(Fixture).where(
        Fixture.season_id == season_id,
        or_(Fixture.home_team_id == team_id, Fixture.away_team_id == team_id),
        Fixture.status == 'finished'
    )
    
    fixtures_result = await db.execute(fixtures_query)
    fixtures = fixtures_result.scalars().all()
    
    # Calculer les statistiques
    stats = {
        "matches_played": len(fixtures),
        "wins": 0,
        "draws": 0,
        "losses": 0,
        "goals_for": 0,
        "goals_against": 0,
        "clean_sheets": 0,
        "failed_to_score": 0
    }
    
    for fixture in fixtures:
        is_home = fixture.home_team_id == team_id
        team_score = fixture.home_score if is_home else fixture.away_score
        opponent_score = fixture.away_score if is_home else fixture.home_score
        
        stats["goals_for"] += team_score or 0
        stats["goals_against"] += opponent_score or 0
        
        if team_score > opponent_score:
            stats["wins"] += 1
        elif team_score == opponent_score:
            stats["draws"] += 1
        else:
            stats["losses"] += 1
        
        if opponent_score == 0:
            stats["clean_sheets"] += 1
        if team_score == 0:
            stats["failed_to_score"] += 1
    
    stats["goal_difference"] = stats["goals_for"] - stats["goals_against"]
    stats["points"] = stats["wins"] * 3 + stats["draws"]
    stats["win_rate"] = round((stats["wins"] / stats["matches_played"]) * 100, 2) if stats["matches_played"] > 0 else 0
    stats["goals_per_match"] = round(stats["goals_for"] / stats["matches_played"], 2) if stats["matches_played"] > 0 else 0
    
    return APIResponse(
        success=True,
        data={
            "team": {
                "id": team.id,
                "name": team.name,
                "logo_url": team.logo_url
            },
            "season_id": season_id,
            "statistics": stats
        }
    )


@router.get("/league/{league_id}/top-teams", response_model=APIResponse)
async def get_league_top_teams(
    league_id: int,
    season_id: Optional[int] = Query(None, description="Filtrer par saison"),
    limit: int = Query(10, ge=1, le=50),
    db: AsyncSession = Depends(get_db)
):
    
    query = select(Standing).join(
        Team, Standing.team_id == Team.id
    ).join(
        Season, Standing.season_id == Season.id
    ).where(Season.league_id == league_id)
    
    if season_id:
        query = query.where(Standing.season_id == season_id)
    
    query = query.order_by(Standing.points.desc()).limit(limit)
    
    result = await db.execute(query)
    standings = result.scalars().all()
    
    teams_data = []
    for standing in standings:
        team_query = select(Team).where(Team.id == standing.team_id)
        team_result = await db.execute(team_query)
        team = team_result.scalar_one()
        
        teams_data.append({
            "rank": standing.rank,
            "team": {
                "id": team.id,
                "name": team.name,
                "logo_url": team.logo_url
            },
            "points": standing.points,
            "wins": standing.wins,
            "draws": standing.draws,
            "losses": standing.losses,
            "goals_for": standing.goals_for,
            "goals_against": standing.goals_against,
            "goal_difference": standing.goal_difference
        })
    
    return APIResponse(
        success=True,
        data={"top_teams": teams_data}
    )