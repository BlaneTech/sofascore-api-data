
from app.db.models import League, Season, TournamentType
from app.utils import get_or_create

async def ingest_league(session, event_data):
   
    league_defaults = {
        "sofascore_id": event_data["tournament"]["uniqueTournament"]["id"],
        "name": event_data["tournament"]["uniqueTournament"]["name"],
        "slug": event_data["tournament"]["uniqueTournament"]["slug"],
        "type": TournamentType.AFCON,
        "country": event_data["tournament"]["uniqueTournament"]["category"]["name"],
        "logo_url": None,
    }
    
    return await get_or_create(
        session, League, "sofascore_id",
        league_defaults["sofascore_id"], league_defaults
    )


async def ingest_season(session, event_data, league_id):
    
    season_defaults = {
        "sofascore_id": event_data["season"]["id"],
        "league_id": league_id,
        "year": event_data["season"]["year"],
        "name": event_data["season"]["name"],
        "current": True,
    }
    
    return await get_or_create(
        session, Season, "sofascore_id",
        season_defaults["sofascore_id"], season_defaults
    )
