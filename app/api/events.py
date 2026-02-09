from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import joinedload
from typing import Optional

from app.db.database import get_db
from app.db.models import MatchEvent, Fixture, Player, Team
from app.schemas import MatchEventSchema, APIResponse, PaginationMeta

router = APIRouter(prefix="/events", tags=["Match Events"])


@router.get("", response_model=APIResponse)
async def get_events(
    fixture_id: Optional[int] = Query(None, description="Filtrer par match"),
    team_id: Optional[int] = Query(None, description="Filtrer par équipe"),
    player_id: Optional[int] = Query(None, description="Filtrer par joueur"),
    type: Optional[str] = Query(None, description="Type d'événement (goal, yellowCard, etc.)"),
    page: int = Query(1, ge=1, description="Numéro de page"),
    per_page: int = Query(20, ge=1, le=100, description="Résultats par page"),
    db: AsyncSession = Depends(get_db)
):
   
    query = select(MatchEvent).options(
        joinedload(MatchEvent.player),
        joinedload(MatchEvent.assist_player),
        joinedload(MatchEvent.fixture)
    )
    
    if fixture_id:
        query = query.where(MatchEvent.fixture_id == fixture_id)
    if team_id:
        query = query.where(MatchEvent.team_id == team_id)
    if player_id:
        query = query.where(MatchEvent.player_id == player_id)
    if type:
        query = query.where(MatchEvent.type == type)
    
    # Compter le total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    # Pagination
    offset = (page - 1) * per_page
    query = query.order_by(MatchEvent.minute).offset(offset).limit(per_page)
    
    result = await db.execute(query)
    events = result.scalars().all()
    
    events_data = [MatchEventSchema.model_validate(event) for event in events]
    
    return APIResponse(
        success=True,
        data={"events": [event.model_dump() for event in events_data]},
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page
        )
    )


@router.get("/goals", response_model=APIResponse)
async def get_goals(
    fixture_id: Optional[int] = Query(None, description="Filtrer par match"),
    team_id: Optional[int] = Query(None, description="Filtrer par équipe"),
    player_id: Optional[int] = Query(None, description="Filtrer par joueur"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    
    query = select(MatchEvent).options(
        joinedload(MatchEvent.player),
        joinedload(MatchEvent.assist_player),
        joinedload(MatchEvent.fixture)
    ).where(MatchEvent.type == 'goal')
    
    if fixture_id:
        query = query.where(MatchEvent.fixture_id == fixture_id)
    if team_id:
        query = query.where(MatchEvent.team_id == team_id)
    if player_id:
        query = query.where(MatchEvent.player_id == player_id)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    offset = (page - 1) * per_page
    query = query.order_by(MatchEvent.minute).offset(offset).limit(per_page)
    
    result = await db.execute(query)
    goals = result.scalars().all()
    
    goals_data = [MatchEventSchema.model_validate(goal) for goal in goals]
    
    return APIResponse(
        success=True,
        data={"goals": [goal.model_dump() for goal in goals_data]},
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page
        )
    )


@router.get("/cards", response_model=APIResponse)
async def get_cards(
    fixture_id: Optional[int] = Query(None, description="Filtrer par match"),
    team_id: Optional[int] = Query(None, description="Filtrer par équipe"),
    player_id: Optional[int] = Query(None, description="Filtrer par joueur"),
    card_type: Optional[str] = Query(None, description="Type de carton (yellow, red)"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    
    from app.db.models import EventType
    
    query = select(MatchEvent).options(
        joinedload(MatchEvent.player),
        joinedload(MatchEvent.fixture)
    )
    
    # Filtrer par type de carton
    if card_type == 'yellow':
        query = query.where(MatchEvent.type == EventType.YELLOW_CARD)
    elif card_type == 'red':
        query = query.where(MatchEvent.type == EventType.RED_CARD)
    else:
        # Tous les cartons
        query = query.where(
            (MatchEvent.type == EventType.YELLOW_CARD) | 
            (MatchEvent.type == EventType.RED_CARD)
        )
    
    if fixture_id:
        query = query.where(MatchEvent.fixture_id == fixture_id)
    if team_id:
        query = query.where(MatchEvent.team_id == team_id)
    if player_id:
        query = query.where(MatchEvent.player_id == player_id)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    offset = (page - 1) * per_page
    query = query.order_by(MatchEvent.minute).offset(offset).limit(per_page)
    
    result = await db.execute(query)
    cards = result.scalars().all()
    
    cards_data = [MatchEventSchema.model_validate(card) for card in cards]
    
    return APIResponse(
        success=True,
        data={"cards": [card.model_dump() for card in cards_data]},
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page
        )
    )


@router.get("/top-scorers", response_model=APIResponse)
async def get_top_scorers(
    league_id: Optional[int] = Query(None, description="Filtrer par league"),
    season_id: Optional[int] = Query(None, description="Filtrer par saison"),
    team_id: Optional[int] = Query(None, description="Filtrer par équipe"),
    limit: int = Query(10, ge=1, le=50, description="Nombre de joueurs"),
    db: AsyncSession = Depends(get_db)
):
    
    from sqlalchemy import and_
    
    # Requête pour compter les buts par joueur
    query = select(
        Player,
        func.count(MatchEvent.id).label('goals')
    ).join(
        MatchEvent, MatchEvent.player_id == Player.id
    ).where(
        MatchEvent.type == 'goal'
    )
    
    # Filtres optionnels
    if league_id or season_id:
        query = query.join(Fixture, MatchEvent.fixture_id == Fixture.id)
        
        if league_id:
            query = query.where(Fixture.league_id == league_id)
        if season_id:
            query = query.where(Fixture.season_id == season_id)
    
    if team_id:
        query = query.where(Player.team_id == team_id)
    
    query = query.group_by(Player.id).order_by(func.count(MatchEvent.id).desc()).limit(limit)
    
    result = await db.execute(query)
    scorers = result.all()
    
    scorers_data = [
        {
            "player": {
                "id": player.id,
                "name": player.name,
                "position": player.position,
                "jersey_number": player.jersey_number,
                "photo_url": player.photo_url
            },
            "goals": goals
        }
        for player, goals in scorers
    ]
    
    return APIResponse(
        success=True,
        data={"top_scorers": scorers_data}
    )