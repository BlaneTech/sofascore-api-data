# scripts/ingest_friendlies.py

import asyncio
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from sofascore_wrapper.api import SofascoreAPI
from sofascore_wrapper.search import Search
from sofascore_wrapper.team import Team
from sofascore_wrapper.match import Match

from app.db import AsyncSessionLocal
from app.services.scraper import (
    ingest_league, ingest_season, ingest_team, ingest_players_for_team,
    ingest_fixture, ingest_lineups, ingest_match_statistics, ingest_match_events
)
from app.services.scraper.manager_service import ingest_managers_for_fixture
from sqlalchemy import select
from app.db.models import Fixture


TEAM_NAME = "senegal"
FRIENDLY_SLUG = "int-friendly-games"


def filter_friendly_matches(matches: list[dict]) -> list[dict]:
    seen = set()
    result = []
    for match in matches:
        if match.get("tournament", {}).get("slug") != FRIENDLY_SLUG:
            continue
        if match["id"] in seen:
            continue
        seen.add(match["id"])
        result.append(match)
    return result


async def ingest_friendly_fixture(session, api, event: dict):

    # Skip si déjà en base
    existing = await session.execute(
        select(Fixture).where(Fixture.sofascore_id == event["id"])
    )
    if existing.scalar_one_or_none():
        print(f"  [{event['id']}] Déjà en base, skip")
        return

    match_status = event.get("status", {}).get("type", "notstarted")
    print(f"  [{event['id']}] {event['homeTeam']['name']} vs {event['awayTeam']['name']} — {match_status}")

    # League & Season
    league_obj = await ingest_league(session, event)
    season_obj = await ingest_season(session, event, league_obj.id)

    # Équipes
    try:
        home_team = await ingest_team(session, api, event["homeTeam"])
        away_team = await ingest_team(session, api, event["awayTeam"])
    except Exception as e:
        print(f"    Erreur équipes: {e}")
        return

    if not home_team or not away_team:
        print(f"    Équipes manquantes, skip")
        return

    # Joueurs
    for sofa_id, team_obj in [
        (event["homeTeam"]["id"], home_team),
        (event["awayTeam"]["id"], away_team),
    ]:
        try:
            await ingest_players_for_team(session, api, sofa_id, team_obj.id)
        except Exception as e:
            print(f"    Erreur joueurs ({sofa_id}): {e}")

    # Managers
    try:
        await ingest_managers_for_fixture(
            session, api, event["id"],
            event["homeTeam"]["id"],
            event["awayTeam"]["id"]
        )
    except Exception as e:
        print(f"    Erreur managers: {e}")

    try:
        fixture = await ingest_fixture(
            session, event, league_obj.id, season_obj.id,
            home_team.id, away_team.id
        )
    except Exception as e:
        print(f"    Erreur fixture: {e}")
        return

    match_obj = Match(api, event["id"])

    if match_status in ("inprogress", "finished"):
        try:
            home_lineups = await match_obj.lineups_home()
            if home_lineups:
                await ingest_lineups(session, fixture.id, home_lineups, event["homeTeam"]["id"])

            away_lineups = await match_obj.lineups_away()
            if away_lineups:
                await ingest_lineups(session, fixture.id, away_lineups, event["awayTeam"]["id"])
        except Exception as e:
            print(f"    Lineups indisponibles: {e}")

    if match_status == "finished":
        try:
            match_stats = await match_obj.stats()
            if match_stats:
                await ingest_match_statistics(
                    session, fixture.id,
                    event["homeTeam"]["id"],
                    event["awayTeam"]["id"],
                    match_stats
                )

            incidents = await match_obj.incidents()
            if incidents:
                await ingest_match_events(
                    session, incidents, fixture.id,
                    home_team.id, away_team.id
                )
        except Exception as e:
            print(f"    Stats/events indisponibles: {e}")


async def main():
    api = SofascoreAPI()

    try:
        search = Search(api, search_string=TEAM_NAME)
        result = await search.search_all(sport="football")
        team_id = result["results"][0]["entity"]["id"]

        team = Team(api, team_id)
        next_matches = await team.next_fixtures()

        friendly_matches = filter_friendly_matches(next_matches)
        print(f"\n{len(friendly_matches)} match(s) amicaux trouvés\n")

        async with AsyncSessionLocal() as session:
            async with session.begin():
                for event in friendly_matches:
                    await asyncio.sleep(1)
                    await ingest_friendly_fixture(session, api, event)

                await session.commit()

        print("\nIngestion matchs amicaux terminée ✓")

    except Exception as e:
        print(f"\nERREUR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await api.close()


if __name__ == "__main__":
    asyncio.run(main())