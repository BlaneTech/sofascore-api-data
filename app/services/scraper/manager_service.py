from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models import Manager, TeamManager, Team
from app.utils.db_helpers import get_or_create
from datetime import datetime, date
from typing import Optional


async def ingest_manager(session: AsyncSession, manager_data: dict) -> Manager:
    
    sofascore_id = manager_data['id']
    
    manager_dict = {
        'sofascore_id': sofascore_id,
        'name': manager_data.get('name'),
        'slug': manager_data.get('slug'),
        'short_name': manager_data.get('shortName'),
    }
    
    short_name = manager_data.get('shortName', '')
    if '. ' in short_name:
        parts = short_name.split('. ', 1)
        manager_dict['first_name'] = parts[0] + '.'
        manager_dict['last_name'] = parts[1]
    else:
        name_parts = manager_data.get('name', '').split(' ', 1)
        if len(name_parts) == 2:
            manager_dict['first_name'] = name_parts[0]
            manager_dict['last_name'] = name_parts[1]
    
    # Nationalité
    if manager_data.get('country'):
        manager_dict['nationality'] = manager_data['country'].get('name')
    
    if manager_data.get('dateOfBirthTimestamp'):
        try:
            dob = datetime.fromtimestamp(manager_data['dateOfBirthTimestamp'])
            manager_dict['date_of_birth'] = dob.date()
        except Exception as e:
            print(f"⚠️  Erreur conversion date de naissance: {e}")
    
    # Photo URL
    manager_dict['photo_url'] = f"https://img.sofascore.com/api/v1/manager/{sofascore_id}/image"
    
    # CORRECTION : Bonne signature de get_or_create
    manager = await get_or_create(
        session,
        Manager,
        'sofascore_id',      # <- nom du champ unique (string)
        sofascore_id,        # <- valeur à chercher
        manager_dict         # <- defaults (dict)
    )
    
    return manager


async def ingest_manager_basic(session: AsyncSession, manager_basic_data: dict) -> int:
    
    sofascore_id = manager_basic_data['id']
    
    manager_dict = {
        'sofascore_id': sofascore_id,
        'name': manager_basic_data.get('name'),
        'slug': manager_basic_data.get('slug'),
    }
    
    # CORRECTION : Bonne signature de get_or_create
    manager = await get_or_create(
        session,
        Manager,
        'sofascore_id',      # <- nom du champ unique (string)
        sofascore_id,        # <- valeur à chercher
        manager_dict         # <- defaults (dict)
    )
    
    return manager.sofascore_id


async def link_manager_to_team(
    session: AsyncSession,
    team_sofascore_id: int,
    manager_data: dict,
    is_current: bool = True
) -> Optional[TeamManager]:

    team_query = select(Team).where(Team.sofascore_id == team_sofascore_id)
    team_result = await session.execute(team_query)
    team = team_result.scalar_one_or_none()
    
    if not team:
        print(f"⚠️  Équipe {team_sofascore_id} introuvable pour lier le manager")
        return None
    
    # Créer ou mettre à jour le manager
    manager = await ingest_manager(session, manager_data)
    
    # Vérifier si la relation existe déjà
    tm_query = select(TeamManager).where(
        TeamManager.team_id == team.id,
        TeamManager.manager_id == manager.id,
        TeamManager.is_current == True
    )
    tm_result = await session.execute(tm_query)
    existing_tm = tm_result.scalar_one_or_none()
    
    if existing_tm:
        # print(f"  ✓ Relation déjà existante: {manager.name} -> {team.name}")
        return existing_tm
    
    # Créer la nouvelle relation
    team_manager = TeamManager(
        team_id=team.id,
        manager_id=manager.id,
        is_current=is_current,
        start_date=None
    )
    session.add(team_manager)
    
    return team_manager


async def ingest_match_managers(
    session: AsyncSession,
    match_id: int,
    managers_data: dict,
    home_team_sofascore_id: int,
    away_team_sofascore_id: int
):
    manager_ids = []
    
    # Manager domicile
    if managers_data.get('homeManager'):
        home_mgr_id = await ingest_manager_basic(session, managers_data['homeManager'])
        manager_ids.append(('home', home_mgr_id, home_team_sofascore_id))
    
    # Manager extérieur
    if managers_data.get('awayManager'):
        away_mgr_id = await ingest_manager_basic(session, managers_data['awayManager'])
        manager_ids.append(('away', away_mgr_id, away_team_sofascore_id))
    
    return manager_ids

async def ingest_managers_for_fixture(
    session: AsyncSession,
    api,
    fixture_id: int,
    home_team_sofascore_id: int,
    away_team_sofascore_id: int
):

    from sofascore_wrapper.match import Match
    from sofascore_wrapper.manager import Manager
    
    try:
        # Récupérer les managers du match
        match_obj = Match(api, fixture_id)
        managers_basic = await match_obj.managers()
        
        if not managers_basic:
            return
        
        # Ingérer les données de base
        manager_ids = await ingest_match_managers(
            session,
            fixture_id,
            managers_basic,
            home_team_sofascore_id,
            away_team_sofascore_id
        )
        
        # 3Récupérer les détails complets et lier aux équipes
        for side, manager_sofascore_id, team_sofascore_id in manager_ids:
            try:
                # Récupérer les détails complets
                manager_obj = Manager(api, manager_sofascore_id)
                manager_details_response = await manager_obj.get_manager()
                
                if not manager_details_response:
                    print(f" Pas de données pour manager {manager_sofascore_id}")
                    continue
                
                manager_details = manager_details_response.get('manager')
                
                if not manager_details or 'id' not in manager_details:
                    print(f" Données manager {manager_sofascore_id} incomplètes")
                    continue
                
                # Lier à l'équipe
                await link_manager_to_team(
                    session,
                    team_sofascore_id,
                    manager_details,
                    is_current=True
                )
                
            except KeyError as e:
                print(f"  Champ manquant pour manager {manager_sofascore_id}: {e}")
                continue
            except Exception as e:
                print(f"  Erreur détails manager {manager_sofascore_id}: {e}")
                continue
        
        # print(f"✓ Managers ingérés pour le match {fixture_id}")
        
    except Exception as e:
        print(f"Erreur ingestion managers du match {fixture_id}: {e}")