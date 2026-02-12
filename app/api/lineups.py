from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from typing import Optional

from app.db.database import get_db
from app.db.models import Lineup, Fixture, Team, Player
from app.schemas import APIResponse, PaginationMeta
from collections import defaultdict


router = APIRouter(prefix="/lineups", tags=["Lineups"])


@router.get("", response_model=APIResponse)
async def get_lineups(
    fixture_id: Optional[int] = Query(None, description="Filtrer par match"),
    team_id: Optional[int] = Query(None, description="Filtrer par équipe"),
    player_id: Optional[int] = Query(None, description="Filtrer par joueur"),
    starter: Optional[bool] = Query(None, description="Titulaires uniquement"),
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
   
    query = select(Lineup).options(
        joinedload(Lineup.player),
        joinedload(Lineup.team),
        joinedload(Lineup.fixture)
    )
    
    if fixture_id:
        query = query.where(Lineup.fixture_id == fixture_id)
    if team_id:
        query = query.where(Lineup.team_id == team_id)
    if player_id:
        query = query.where(Lineup.player_id == player_id)
    if starter is not None:
        query = query.where(Lineup.starter == starter)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page)
    
    # result = await db.execute(query)
    result = await db.execute(query)
    lineups = result.scalars().all()
    

    from collections import defaultdict

    lineups_data = {
        "fixture": None,
        "teams": []
    }

    teams_dict = {}

    for lineup in lineups:
        # Fixture défini une seule fois
        if lineups_data["fixture"] is None and lineup.fixture:
            lineups_data["fixture"] = {
                "id": lineup.fixture.id,
                "home_team": lineup.fixture.home_team.name if lineup.fixture.home_team else None,
                "away_team": lineup.fixture.away_team.name if lineup.fixture.away_team else None,
                "round": getattr(lineup.fixture, "round", None),
                "group": getattr(lineup.fixture, "group", None),
                "stage": getattr(lineup.fixture, "stage", None),
                "status": getattr(lineup.fixture, "status", None),
                "start_time": getattr(lineup.fixture, "start_time", None),
                "home_score": getattr(lineup.fixture, "home_score", None),
                "away_score": getattr(lineup.fixture, "away_score", None)
            }

        # Équipe regroupée
        if lineup.team:
            team_id = lineup.team.id
            if team_id not in teams_dict:
                teams_dict[team_id] = {
                    "id": lineup.team.id,
                    "name": lineup.team.name,
                    "formation": lineup.formation,
                    "starters": [],
                    "substitutes": []
                }

            # Joueur ajouté dans starters ou substitutes
            player_data = {
                "id": lineup.player.id,
                "name": lineup.player.name,
                "position": lineup.player.position,
                "jersey_number": lineup.player.jersey_number,
                "captain": lineup.captain,
                "rating": lineup.rating,
                "minutes_played": lineup.minutes_played
            }

            if lineup.starter:
                teams_dict[team_id]["starters"].append(player_data)
            elif lineup.substitute:
                teams_dict[team_id]["substitutes"].append(player_data)

    # Finalisation
    lineups_data["teams"] = list(teams_dict.values())



    return APIResponse(
        success=True,
        data={"lineups": lineups_data},
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page
        )
    )


@router.get("/player/{player_id}/history", response_model=APIResponse)
async def get_player_lineup_history(
    player_id: int,
    season_id: Optional[int] = Query(None, description="Filtrer par saison"),
    starter_only: bool = Query(False, description="Titularisations uniquement"),
    db: AsyncSession = Depends(get_db)
):
    
    # Vérifier que le joueur existe
    player_query = select(Player).where(Player.id == player_id)
    player_result = await db.execute(player_query)
    player = player_result.scalar_one_or_none()
    
    if not player:
        raise HTTPException(status_code=404, detail="Player not found")
    
    query = (
        select(Lineup)
        .join(Lineup.fixture)
        .options(
            joinedload(Lineup.fixture).joinedload(Fixture.home_team),
            joinedload(Lineup.fixture).joinedload(Fixture.away_team),
            joinedload(Lineup.team)
        )
        .where(Lineup.player_id == player_id)
    )
    
    if season_id:
        query = query.join(Fixture).where(Fixture.season_id == season_id)
    
    if starter_only:
        query = query.where(Lineup.starter == True)
    
    query = query.order_by(Fixture.date.desc())
    
    result = await db.execute(query)
    lineups = result.scalars().unique().all()
    
    # Statistiques globales
    total_appearances = len(lineups)
    starts = len([l for l in lineups if l.starter])
    substitute_appearances = total_appearances - starts
    
    lineups_data = []
    for lineup in lineups:
        lineups_data.append({
            "fixture": {
                "id": lineup.fixture.id,
                "date": lineup.fixture.date.isoformat() if lineup.fixture.date else None,
                "home_team": lineup.fixture.home_team.name if lineup.fixture.home_team else None,
                "away_team": lineup.fixture.away_team.name if lineup.fixture.away_team else None,
                "score": f"{lineup.fixture.home_score or 0} - {lineup.fixture.away_score or 0}"
            },
            "starter": lineup.starter,
            "captain": lineup.captain,
            "minutes_played": lineup.minutes_played,
            "rating": lineup.rating,
            "position": lineup.position
        })
    
    return APIResponse(
        success=True,
        data={
            "player": {
                "id": player.id,
                "name": player.name,
                "position": player.position
            },
            "summary": {
                "total_appearances": total_appearances,
                "starts": starts,
                "substitute_appearances": substitute_appearances,
                "minutes_played": sum(l.minutes_played or 0 for l in lineups),
                "captain_appearances": len([l for l in lineups if l.captain])
            },
            "lineups": lineups_data
        }
    )


@router.get("/team/{team_id}/most-used-formation", response_model=APIResponse)
async def get_team_most_used_formation(
    team_id: int,
    season_id: Optional[int] = Query(None, description="Filtrer par saison"),
    db: AsyncSession = Depends(get_db)
):
    
    # Vérifier que l'équipe existe
    team_query = select(Team).where(Team.id == team_id)
    team_result = await db.execute(team_query)
    team = team_result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    query = select(
        Lineup.formation,
        func.count(func.distinct(Lineup.fixture_id)).label('usage_count')
    ).where(
        Lineup.team_id == team_id,
        Lineup.formation.isnot(None)
    )
    
    if season_id:
        query = query.join(Fixture).where(Fixture.season_id == season_id)
    
    query = query.group_by(Lineup.formation).order_by(func.count(func.distinct(Lineup.fixture_id)).desc())
    
    result = await db.execute(query)
    formations = result.all()
    
    formations_data = [
        {
            "formation": formation,
            "matches_used": count
        }
        for formation, count in formations
    ]
    
    return APIResponse(
        success=True,
        data={
            "team": {
                "id": team.id,
                "name": team.name
            },
            "formations": formations_data,
            "most_used": formations_data[0] if formations_data else None
        }
    )


@router.get("/fixture/{fixture_id}/captains", response_model=APIResponse)
async def get_fixture_captains(
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
    
    # Récupérer les capitaines
    captains_query = select(Lineup).options(
        joinedload(Lineup.player),
        joinedload(Lineup.team)
    ).where(
        Lineup.fixture_id == fixture_id,
        Lineup.captain == True
    )
    
    result = await db.execute(captains_query)
    captains = result.scalars().all()
    
    captains_data = []
    for captain in captains:
        captains_data.append({
            "team": {
                "id": captain.team.id,
                "name": captain.team.name
            },
            "player": {
                "id": captain.player.id,
                "name": captain.player.name,
                "position": captain.player.position,
                "jersey_number": captain.player.jersey_number,
                "photo_url": captain.player.photo_url
            }
        })
    
    return APIResponse(
        success=True,
        data={
            "fixture": {
                "id": fixture.id,
                "home_team": fixture.home_team.name,
                "away_team": fixture.away_team.name
            },
            "captains": captains_data
        }
    )