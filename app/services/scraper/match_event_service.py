from sqlalchemy import select
from app.db.models import MatchEvent, Player, Team, EventType
from app.utils import get_or_create

async def ingest_match_events(session, incidents_data, fixture_id, home_team_id, away_team_id):
    
    for incident in incidents_data.get("incidents", []):
        incident_type = incident.get("incidentType")
        
        if incident_type in ["period", "injuryTime"]:
            continue
        
        event_type = _map_incident_to_event_type(incident_type, incident)
        if not event_type:
            print(f"Type d'incident inconnu: {incident_type}")
            continue
        
        is_home = incident.get("isHome", True)
        team_id = home_team_id if is_home else away_team_id
        
        # Récupérer le joueur principal
        player_id = None
        if "player" in incident:
            player_id = await _get_player_id(session, incident["player"]["id"])
           
        # Récupérer le passeur
        assist_player_id = None
        if "assist1" in incident:
            assist_player_id = await _get_player_id(session, incident["assist1"]["id"])
        
        # Récupérer le joueur sortant
        player_out_id = None
        if incident_type == "substitution" and "playerOut" in incident:
            player_out_id = await _get_player_id(session, incident["playerOut"]["id"])

            if "playerIn" in incident:
                player_id = await _get_player_id(session, incident["playerIn"]["id"])
        
        # Construire l'objet event
        event_defaults = {
            "sofascore_id": incident.get("id"),
            "fixture_id": fixture_id,
            "team_id": team_id,
            "player_id": player_id,
            "assist_player_id": assist_player_id,
            "player_out_id": player_out_id,
            "type": event_type,
            "minute": incident.get("time", 0),
            "extra_minute": incident.get("addedTime"),
            "is_home": is_home,
            "home_score": incident.get("homeScore"),
            "away_score": incident.get("awayScore"),
            "incident_class": incident.get("incidentClass"),
            "reason": incident.get("reason"),
            "detail": _build_event_detail(incident),
            "comments": incident.get("description"),
        }
        
        if not event_defaults["sofascore_id"]:
            print(f"Event sans ID Sofascore, ignoré: {incident_type}")
            continue
        
        await get_or_create(
            session, MatchEvent, "sofascore_id",
            event_defaults["sofascore_id"], event_defaults
        )
        
        player_name = incident.get("player", {}).get("name", "N/A") if "player" in incident else "N/A"
        # print(f"  Event {event_type.value} - {incident.get('time', 0)}' - {player_name}")

def _map_incident_to_event_type(incident_type: str, incident: dict) -> EventType:
    
    mapping = {
        "goal": EventType.GOAL,
        "card": EventType.YELLOW_CARD if incident.get("incidentClass") == "yellow" else EventType.RED_CARD,
        "substitution": EventType.SUBSTITUTION,
        "inGamePenalty": EventType.PENALTY_MISSED if incident.get("incidentClass") == "missed" else EventType.GOAL,
        "varDecision": EventType.VAR,
    }
    
    return mapping.get(incident_type)


async def _get_player_id(session, sofascore_player_id: int):
   
    result = await session.execute(
        select(Player).where(Player.sofascore_id == sofascore_player_id)
    )
    player = result.scalar_one_or_none()
    
    if not player:
        print(f"Player ID {sofascore_player_id} non trouvé")
        return None
    
    return player.id


def _build_event_detail(incident: dict) -> str:

    incident_type = incident.get("incidentType")
    
    if incident_type == "goal":
        player_name = incident.get("player", {}).get("name", "Unknown")
        assist_name = incident.get("assist1", {}).get("name", "")
        if assist_name:
            return f"{player_name} (assist: {assist_name})"
        return player_name
    
    elif incident_type == "card":
        player_name = incident.get("playerName", "Unknown")
        reason = incident.get("reason", "")
        return f"{player_name} - {reason}"
    
    elif incident_type == "substitution":
        player_in = incident.get("playerIn", {}).get("name", "Unknown")
        player_out = incident.get("playerOut", {}).get("name", "Unknown")
        return f"IN: {player_in} | OUT: {player_out}"
    
    elif incident_type == "inGamePenalty":
        player_name = incident.get("player", {}).get("name", "Unknown")
        return f"Penalty - {player_name}"
    
    return