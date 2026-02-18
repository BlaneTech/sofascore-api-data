
from datetime import datetime
from app.db.models import Fixture, MatchStatus
from app.utils import get_or_create


async def ingest_fixture(session, event_data, league_id, season_id, home_team_id, away_team_id):
   
    fixture_defaults = {
        "sofascore_id": event_data["id"],
        "league_id": league_id,
        "season_id": season_id,
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "date": datetime.fromtimestamp(event_data["startTimestamp"]),
        "timestamp": event_data["startTimestamp"],
        "round": event_data.get("roundInfo", {}).get("round"),
        "round_name": f"Round {event_data.get('roundInfo', {}).get('round')}" if event_data.get("roundInfo", {}).get("round") else None,
        "group_name": event_data.get("tournament", {}).get("groupName"),
        "group_sign": event_data.get("tournament", {}).get("groupSign"),
        "status": MatchStatus(event_data.get("status", {}).get("type", "notstarted")),
        "home_score": event_data.get("homeScore", {}).get("current"),
        "away_score": event_data.get("awayScore", {}).get("current"),
        "home_score_period1": event_data.get("homeScore", {}).get("period1"),
        "home_score_period2": event_data.get("homeScore", {}).get("period2"),
        "home_score_normaltime": event_data.get("homeScore", {}).get("normaltime"),
        "away_score_period1": event_data.get("awayScore", {}).get("period1"),
        "away_score_period2": event_data.get("awayScore", {}).get("period2"),
        "away_score_normaltime": event_data.get("awayScore", {}).get("normaltime"),
    }
    
    return await get_or_create(
        session, Fixture, "sofascore_id",
        fixture_defaults["sofascore_id"], fixture_defaults
    )


async def ingest_fixture_from_cup_tree(session, event_id, block_data, round_data, 
                                       league_id, season_id, home_team_id, away_team_id):
    fixture_defaults = {
        "sofascore_id": event_id,
        "league_id": league_id,
        "season_id": season_id,
        "home_team_id": home_team_id,
        "away_team_id": away_team_id,
        "date": datetime.fromtimestamp(block_data['seriesStartDateTimestamp']),
        "timestamp": block_data['seriesStartDateTimestamp'],
        "round": round_data['order'],
        "round_name": round_data['description'],
        "status": MatchStatus.FINISHED if block_data.get('finished') else MatchStatus.NOT_STARTED,
        "home_score": int(block_data.get('homeTeamScore', '0').split()[0]) if block_data.get('homeTeamScore') else None,
        "away_score": int(block_data.get('awayTeamScore', '0').split()[0]) if block_data.get('awayTeamScore') else None,
    }
    
    return await get_or_create(
        session, Fixture, "sofascore_id",
        event_id, fixture_defaults
    )
