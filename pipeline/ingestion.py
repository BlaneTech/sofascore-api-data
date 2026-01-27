import asyncio
from datetime import datetime
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from sofascore_wrapper.api import SofascoreAPI
from sofascore_wrapper.search import Search
from sofascore_wrapper.league import League

from new_models import (
    League as LeagueModel, Season, Team, Fixture,
    TournamentType, MatchStatus
)

DATABASE_URL = "postgresql+asyncpg://football_user:password@localhost:5432/football_db"

engine = create_async_engine(DATABASE_URL, echo=True)
async_session = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

async def get_or_create(session, model, unique_field, value, defaults):
    # Get or create an object by unique field
    result = await session.execute(
        model.__table__.select().where(getattr(model, unique_field) == value)
    )
    row = result.first()
    if row:
        return await session.get(model, row[0])
    obj = model(**defaults)
    session.add(obj)
    await session.flush()
    return obj

async def map_json_to_db(json_data, session):
    for event in json_data["events"]:
        # League
        league_defaults = {
            "sofascore_id": event["tournament"]["uniqueTournament"]["id"],
            "name": event["tournament"]["uniqueTournament"]["name"],
            "slug": event["tournament"]["uniqueTournament"]["slug"],
            "type": TournamentType.AFCON,
            "country": event["tournament"]["uniqueTournament"]["category"]["name"],
            "logo_url": None,
        }
        league = await get_or_create(session, LeagueModel, "sofascore_id",
                                     league_defaults["sofascore_id"], league_defaults)

        # Season
        season_defaults = {
            "sofascore_id": event["season"]["id"],
            "league_id": league.id,
            "year": event["season"]["year"],
            "name": event["season"]["name"],
            "current": True,
        }
        season = await get_or_create(session, Season, "sofascore_id",
                                     season_defaults["sofascore_id"], season_defaults)

        # Teams
        for side in ["homeTeam", "awayTeam"]:
            t = event[side]
            team_defaults = {
                "sofascore_id": t["id"],
                "name": t["name"],
                "slug": t["slug"],
                "short_name": t.get("shortName"),
                "code": t.get("nameCode"),
                "country": t["country"]["name"],
                "national": t.get("national", True),
                "logo_url": None,
                "primary_color": t["teamColors"]["primary"],
                "secondary_color": t["teamColors"]["secondary"],
                "raw_data": t,
            }
            team = await get_or_create(session, Team, "sofascore_id",
                                       team_defaults["sofascore_id"], team_defaults)
            if side == "homeTeam":
                home_team = team
            else:
                away_team = team

        # 4. Fixture
        fixture_defaults = {
            "sofascore_id": event["id"],
            "league_id": league.id,
            "season_id": season.id,
            "home_team_id": home_team.id,
            "away_team_id": away_team.id,
            "date": datetime.fromtimestamp(event["startTimestamp"]),
            "timestamp": event["startTimestamp"],
            "round": event["roundInfo"]["round"],
            "round_name": f"Round {event['roundInfo']['round']}",
            "group_name": event["tournament"].get("groupName"),
            "group_sign": event["tournament"].get("groupSign"),
            "status": MatchStatus(event["status"]["type"]),
            "home_score": event["homeScore"]["current"],
            "away_score": event["awayScore"]["current"],
            "home_score_period1": event["homeScore"]["period1"],
            "home_score_period2": event["homeScore"]["period2"],
            "home_score_normaltime": event["homeScore"]["normaltime"],
            "away_score_period1": event["awayScore"]["period1"],
            "away_score_period2": event["awayScore"]["period2"],
            "away_score_normaltime": event["awayScore"]["normaltime"],
            "raw_data": event,
        }
        await get_or_create(session, Fixture, "sofascore_id",
                            fixture_defaults["sofascore_id"], fixture_defaults)


async def main():
    api = SofascoreAPI()

    # Chercher la compétition CAN
    search = Search(api, search_string="Africa Cup of Nations")
    competition = await search.search_all()
    can_id = competition['results'][0]['entity']['id']

    # Récupérer saisons
    can_league = League(api, can_id)
    can_seasons = await can_league.get_seasons()
    latest_can_season_id = can_seasons[0].get('id') if can_seasons else None

    # Récupérer tous les rounds
    can_rounds = await can_league.rounds(latest_can_season_id)
    rounds_list = [r['round'] for r in can_rounds['rounds']]

    async with async_session() as session:
        async with session.begin():
            # Boucler sur tous les rounds
            for round_number in rounds_list:
                try:
                    match_can = await can_league.league_fixtures_per_round(latest_can_season_id, round_number)
                    await map_json_to_db(match_can, session)
                    print(f"✓ Round {round_number} inséré")
                except Exception as e:
                    print(f"Erreur round {round_number}: {str(e)}")
                    continue

        await session.commit()

    await api.close()

if __name__ == "__main__":
    asyncio.run(main())
