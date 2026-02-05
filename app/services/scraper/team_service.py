
from datetime import datetime
from sofascore_wrapper.team import Team as TeamWrapper
from app.db.models import Team, Player
from app.utils import get_or_create


async def ingest_team(session, api, team_data):
    
    team_id = team_data["id"]
    
    # Récupérer le drapeau de l'équipe
    team_flag_url = None
    try:
        team_wrapper = TeamWrapper(api, team_id)
        team_flag_url = await team_wrapper.image()
    except Exception as e:
        print(f"⚠ Erreur récupération drapeau {team_data['name']}: {str(e)}")
    
    team_defaults = {
        "sofascore_id": team_id,
        "name": team_data["name"],
        "slug": team_data["slug"],
        "short_name": team_data.get("shortName"),
        "code": team_data.get("nameCode"),
        "country": team_data["country"]["name"],
        "national": team_data.get("national", True),
        "logo_url": team_flag_url,
        "primary_color": team_data["teamColors"]["primary"],
        "secondary_color": team_data["teamColors"]["secondary"],
    }
    
    return await get_or_create(
        session, Team, "sofascore_id",
        team_defaults["sofascore_id"], team_defaults
    )


async def ingest_players_for_team(session, api, team_sofascore_id, team_db_id):
    
    try:
        team_wrapper = TeamWrapper(api, team_sofascore_id)
        squad_data = await team_wrapper.squad()
        
        if not squad_data or 'players' not in squad_data:
            print(f"⚠ Pas de données squad pour l'équipe {team_sofascore_id}")
            return
        
        for player_item in squad_data.get('players', []):
            player_data = player_item.get('player', {})
            
            if not player_data or 'id' not in player_data:
                continue
            
            await ingest_player(session, player_data, team_db_id)
    
    except Exception as e:
        print(f"⚠ Erreur ingestion joueurs équipe {team_sofascore_id}: {str(e)}")


async def ingest_player(session, player_data, team_db_id=None):
    
    sofascore_id = player_data.get('id')
    
    player_defaults = {
        'sofascore_id': sofascore_id,
        'team_id': team_db_id,
        'name': player_data.get('name'),
        'first_name': player_data.get('firstName'),
        'last_name': player_data.get('lastName'),
        'slug': player_data.get('slug'),
        'short_name': player_data.get('shortName'),
        'position': player_data.get('position'),
        'jersey_number': int(player_data.get('jerseyNumber') or player_data.get('shirtNumber') or 0) 
                         if (player_data.get('jerseyNumber') or player_data.get('shirtNumber')) else None,
        'height': player_data.get('height'),
        'date_of_birth': None,
        'preferred_foot': player_data.get('preferredFoot'), 
        'photo_url': None,
    }
    
    # Conversion de la date de naissance
    dob_str = player_data.get('dateOfBirth')
    if dob_str:
        try:
            player_defaults['date_of_birth'] = datetime.fromisoformat(
                dob_str.replace('Z', '+00:00')
            ).date()
        except:
            pass
    
    return await get_or_create(
        session, Player, "sofascore_id",
        player_defaults["sofascore_id"], player_defaults
    )
