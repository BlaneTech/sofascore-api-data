from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from sqlalchemy.orm import joinedload
from typing import Optional

from app.db.database import get_db
from app.db.models import Manager, TeamManager, Team
from app.schemas import APIResponse, PaginationMeta

router = APIRouter(prefix="/managers", tags=["Managers"])


@router.get("", response_model=APIResponse)
async def get_managers(
    nationality: Optional[str] = Query(None, description="Filtrer par nationalité"),
    current_only: bool = Query(False, description="Entraîneurs actifs uniquement"),
    search: Optional[str] = Query(None, description="Rechercher par nom"),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    query = select(Manager)
    
    if nationality:
        query = query.where(Manager.nationality.ilike(f"%{nationality}%"))
    if search:
        query = query.where(
            or_(
                Manager.name.ilike(f"%{search}%"),
                Manager.first_name.ilike(f"%{search}%"),
                Manager.last_name.ilike(f"%{search}%")
            )
        )
    
    if current_only:
        query = query.join(TeamManager).where(TeamManager.is_current == True)
    
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()
    
    offset = (page - 1) * per_page
    query = query.offset(offset).limit(per_page).order_by(Manager.name)
    
    result = await db.execute(query)
    managers = result.scalars().all()
    
    managers_data = []
    for manager in managers:
        managers_data.append({
            "id": manager.id,
            "sofascore_id": manager.sofascore_id,
            "name": manager.name,
            "first_name": manager.first_name,
            "last_name": manager.last_name,
            "nationality": manager.nationality,
            "date_of_birth": manager.date_of_birth.isoformat() if manager.date_of_birth else None,
            "photo_url": manager.photo_url
        })
    
    return APIResponse(
        success=True,
        data={"managers": managers_data},
        meta=PaginationMeta(
            page=page,
            per_page=per_page,
            total=total,
            total_pages=(total + per_page - 1) // per_page
        )
    )


@router.get("/{manager_id}", response_model=APIResponse)
async def get_manager(
    manager_id: int,
    db: AsyncSession = Depends(get_db)
):
    
    query = select(Manager).where(Manager.id == manager_id)
    result = await db.execute(query)
    manager = result.scalar_one_or_none()
    
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    
    manager_data = {
        "id": manager.id,
        "sofascore_id": manager.sofascore_id,
        "name": manager.name,
        "slug": manager.slug,
        "first_name": manager.first_name,
        "last_name": manager.last_name,
        "nationality": manager.nationality,
        "date_of_birth": manager.date_of_birth.isoformat() if manager.date_of_birth else None,
        "photo_url": manager.photo_url,
        "created_at": manager.created_at.isoformat() if manager.created_at else None
    }
    
    return APIResponse(
        success=True,
        data={"manager": manager_data}
    )


@router.get("/{manager_id}/teams", response_model=APIResponse)
async def get_manager_teams(
    manager_id: int,
    current_only: bool = Query(False, description="Équipe actuelle uniquement"),
    db: AsyncSession = Depends(get_db)
):
    
    # Vérifier que l'entraîneur existe
    manager_query = select(Manager).where(Manager.id == manager_id)
    manager_result = await db.execute(manager_query)
    manager = manager_result.scalar_one_or_none()
    
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    
    query = select(TeamManager).options(
        joinedload(TeamManager.team)
    ).where(TeamManager.manager_id == manager_id)
    
    if current_only:
        query = query.where(TeamManager.is_current == True)
    
    query = query.order_by(TeamManager.start_date.desc())
    
    result = await db.execute(query)
    team_managers = result.scalars().all()
    
    teams_data = []
    for tm in team_managers:
        teams_data.append({
            "team": {
                "id": tm.team.id,
                "name": tm.team.name,
                "logo_url": tm.team.logo_url
            },
            "start_date": tm.start_date.isoformat() if tm.start_date else None,
            "end_date": tm.end_date.isoformat() if tm.end_date else None,
            "is_current": tm.is_current,
            "duration_days": (tm.end_date - tm.start_date).days if tm.end_date and tm.start_date else None
        })
    
    return APIResponse(
        success=True,
        data={
            "manager": {
                "id": manager.id,
                "name": manager.name
            },
            "teams": teams_data,
            "total_teams": len(teams_data)
        }
    )


@router.get("/{manager_id}/statistics", response_model=APIResponse)
async def get_manager_statistics(
    manager_id: int,
    db: AsyncSession = Depends(get_db)
):
   
    # Vérifier que l'entraîneur existe
    manager_query = select(Manager).where(Manager.id == manager_id)
    manager_result = await db.execute(manager_query)
    manager = manager_result.scalar_one_or_none()
    
    if not manager:
        raise HTTPException(status_code=404, detail="Manager not found")
    
    # Récupérer l'historique
    query = select(TeamManager).where(TeamManager.manager_id == manager_id)
    result = await db.execute(query)
    team_managers = result.scalars().all()
    
    # Calculer les statistiques
    total_teams = len(team_managers)
    current_teams = len([tm for tm in team_managers if tm.is_current])
    
    total_days = 0
    for tm in team_managers:
        if tm.start_date:
            end = tm.end_date or datetime.now().date()
            total_days += (end - tm.start_date).days
    
    from datetime import datetime
    
    stats = {
        "total_teams_managed": total_teams,
        "current_teams": current_teams,
        "total_days_as_manager": total_days,
        "average_tenure_days": round(total_days / total_teams) if total_teams > 0 else 0
    }
    
    return APIResponse(
        success=True,
        data={
            "manager": {
                "id": manager.id,
                "name": manager.name
            },
            "statistics": stats
        }
    )


@router.get("/team/{team_id}/history", response_model=APIResponse)
async def get_team_managers_history(
    team_id: int,
    db: AsyncSession = Depends(get_db)
):

    # Vérifier que l'équipe existe
    team_query = select(Team).where(Team.id == team_id)
    team_result = await db.execute(team_query)
    team = team_result.scalar_one_or_none()
    
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")
    
    query = select(TeamManager).options(
        joinedload(TeamManager.manager)
    ).where(TeamManager.team_id == team_id).order_by(TeamManager.start_date.desc())
    
    result = await db.execute(query)
    team_managers = result.scalars().all()
    
    managers_data = []
    for tm in team_managers:
        managers_data.append({
            "manager": {
                "id": tm.manager.id,
                "name": tm.manager.name,
                "nationality": tm.manager.nationality,
                "photo_url": tm.manager.photo_url
            },
            "start_date": tm.start_date.isoformat() if tm.start_date else None,
            "end_date": tm.end_date.isoformat() if tm.end_date else None,
            "is_current": tm.is_current,
            "duration_days": (tm.end_date - tm.start_date).days if tm.end_date and tm.start_date else None
        })
    
    return APIResponse(
        success=True,
        data={
            "team": {
                "id": team.id,
                "name": team.name
            },
            "managers": managers_data,
            "total_managers": len(managers_data),
            "current_manager": next((m for m in managers_data if m["is_current"]), None)
        }
    )