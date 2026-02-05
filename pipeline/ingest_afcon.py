import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire parent au path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sofascore_wrapper.api import SofascoreAPI
from sofascore_wrapper.search import Search
from sofascore_wrapper.league import League
from sofascore_wrapper.match import Match

from app.db import AsyncSessionLocal
from app.db.models import League as LeagueModel, Season, Fixture
from app.services.scraper import (
    ingest_league, ingest_season, ingest_team, ingest_players_for_team,
    ingest_fixture, ingest_lineups, ingest_match_statistics,
    ingest_cup_tree_matches, ingest_standings, ingest_match_events
)
from app.utils import get_or_create


async def process_round_fixtures(session, api, league_obj, season_obj, match_data):
    
    for event in match_data["events"]:
        try:
            # Ingérer league et season si besoin
            if not league_obj:
                league_obj = await ingest_league(session, event)
                season_obj = await ingest_season(session, event, league_obj.id)
            
            # Ingérer les équipes
            home_team = await ingest_team(session, api, event["homeTeam"])
            away_team = await ingest_team(session, api, event["awayTeam"])
            
            # Ingérer les joueurs
            await ingest_players_for_team(session, api, event["homeTeam"]["id"], home_team.id)
            await ingest_players_for_team(session, api, event["awayTeam"]["id"], away_team.id)
            
            # Ingérer le fixture
            fixture = await ingest_fixture(
                session, event, league_obj.id, season_obj.id,
                home_team.id, away_team.id
            )
            
            # Ingérer les lineups
            match_obj = Match(api, event["id"])
            home_lineups = await match_obj.lineups_home()
            away_lineups = await match_obj.lineups_away()
            
            if home_lineups:
                await ingest_lineups(session, fixture.id, home_lineups, event["homeTeam"]["id"])
            if away_lineups:
                await ingest_lineups(session, fixture.id, away_lineups, event["awayTeam"]["id"])
            
            # Ingérer les statistiques
            match_stats = await match_obj.stats()
            if match_stats:
                await ingest_match_statistics(
                    session, fixture.id,
                    event["homeTeam"]["id"],
                    event["awayTeam"]["id"],
                    match_stats
                )
            
            # Ingérer les événements du match
            match_incidents = await match_obj.incidents()
            if match_incidents:
                await ingest_match_events(
                    session, match_incidents, fixture.id,
                    home_team.id, away_team.id
                )

            # print(f" Match {event['id']} traité avec succès")
            
        except Exception as e:
            print(f" Erreur match {event['id']}: {str(e)}")
            continue
    
    return league_obj, season_obj


async def main():
    api = SofascoreAPI()

    try:
        # Rechercher la compétition AFCON
        print("\n Recherche de la compétition")
        search = Search(api, search_string="Africa Cup of Nations")
        competition = await search.search_all()
        can_id = competition['results'][0]['entity']['id']
        print(f"✓ AFCON trouvée (ID: {can_id})")

        # Récupérer les saisons
        can_league = League(api, can_id)
        can_seasons = await can_league.get_seasons()
        latest_can_season_id = can_seasons[0].get('id') if can_seasons else None
        print(f"Dernière saison (ID: {latest_can_season_id})")

        # Récupérer tous les rounds
        can_rounds = await can_league.rounds(latest_can_season_id)
        rounds_list = [r['round'] for r in can_rounds['rounds']]
        print(f" {len(rounds_list)} rounds trouvés")

        async with AsyncSessionLocal() as session:
            async with session.begin():
                league_obj = None
                season_obj = None
                
                # PHASE DE GROUPES
                print("\n" + "="*50)
                print("📥 INGESTION PHASE DE GROUPES")
                print("="*50 + "\n")
                
                for round_number in rounds_list:
                    try:
                        print(f"\n--- Round {round_number} ---")
                        match_can = await can_league.league_fixtures_per_round(
                            latest_can_season_id, round_number
                        )

                        league_obj, season_obj = await process_round_fixtures(
                            session, api, league_obj, season_obj, match_can
                        )

                    except Exception as e:
                        print(f"✗ Erreur round {round_number}: {str(e)}")
                        continue

                # PHASES FINALES (CUP TREE)
                print("\n" + "="*50)
                print("📥 INGESTION PHASES FINALES")
                print("="*50 + "\n")
                
                if league_obj and season_obj:
                    await ingest_cup_tree_matches(
                        session, api, latest_can_season_id, 
                        league_obj, season_obj
                    )
                else:
                    print("Impossible de récupérer league/season pour cup_tree")

            # CLASSEMENTS
            print("\n" + "="*50)
            print("📥 INGESTION CLASSEMENTS")
            print("="*50 + "\n")

            standings_data = await can_league.standings(latest_can_season_id)
            if standings_data:
                await ingest_standings(session, standings_data, season_obj.id)
                print("\n✓ Classements ingérés avec succès")
            else:
                print("✗ Aucune donnée de classement disponible")

            await session.commit()
            print("\n" + "="*50)
            print(" INGESTION TERMINÉE AVEC SUCCÈS!")
            print("="*50 + "\n")

    except Exception as e:
        print(f"\n ERREUR FATALE: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        await api.close()


if __name__ == "__main__":
    asyncio.run(main())
