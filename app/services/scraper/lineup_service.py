
from app.db.models import Lineup, Player, Team
from app.utils import get_or_create, get_team_by_sofascore_id


async def ingest_lineups(session, fixture_id, lineup_data, team_sofascore_id):

    # Récupérer l'équipe par son sofascore_id
    team_db_id, _ = await get_team_by_sofascore_id(session, Team, team_sofascore_id)
    
    if not team_db_id:
        print(f"⚠ Équipe {team_sofascore_id} introuvable")
        return
    
    # Insérer les starters
    for starter in lineup_data.get("starters", []):
        await _insert_player_lineup(
            session, fixture_id, team_db_id, 
            starter, lineup_data, is_substitute=False
        )
    
    # Insérer les substitutes
    for sub in lineup_data.get("substitutes", []):
        await _insert_player_lineup(
            session, fixture_id, team_db_id, 
            sub, lineup_data, is_substitute=True
        )


async def _insert_player_lineup(session, fixture_id, team_db_id, player_block, 
                                lineup_data, is_substitute=False):
    p = player_block["player"]
    
    # Créer ou récupérer le joueur
    player_defaults = {
        "sofascore_id": p["id"],
        "name": p["name"],
        "slug": p.get("slug"),
        "short_name": p.get("shortName"),
        "first_name": p.get("firstName"),
        "last_name": p.get("lastName"),
        "position": p.get("position"),
        "jersey_number": int(p.get("jerseyNumber")) if p.get("jerseyNumber") else None,
        "height": p.get("height"),
    }
    player = await get_or_create(
        session, Player, "sofascore_id",
        player_defaults["sofascore_id"], player_defaults
    )
    
    # Créer le lineup
    lineup_defaults = {
        "fixture_id": fixture_id,
        "team_id": team_db_id,
        "player_id": player.id,
        "formation": lineup_data.get("formation"),
        "position": player_block.get("position"),
        "starter": not is_substitute,
        "rating": player_block.get("statistics", {}).get("rating"),
        "minutes_played": player_block.get("statistics", {}).get("minutesPlayed"),
        "captain": player_block.get("captain", False),
        "substitute": is_substitute,
    }
    
    await get_or_create(
        session, Lineup, 
        "player_id", lineup_defaults["player_id"], lineup_defaults
    )
