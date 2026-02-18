import asyncio
import sys
from pathlib import Path
from datetime import datetime

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
from app.services.scraper.manager_service import ingest_managers_for_fixture
from app.services.scraper.statistics_service import (
    ingest_all_players_statistics,
    ingest_all_teams_statistics
)
from app.utils import get_or_create
from sqlalchemy import select

# async def process_round_fixtures(session, api, league_obj, season_obj, match_data):
    
#     for event in match_data["events"]:
#         try:
#             # Vérifier si match existe déjà
#             fixture_query = select(Fixture).where(Fixture.sofascore_id == event["id"])
#             fixture_result = await session.execute(fixture_query)
#             existing_fixture = fixture_result.scalar_one_or_none()
            
#             if existing_fixture:
#                 print(f"  Match {event['id']} déjà ingéré, skip")
#                 continue
            
#             if not league_obj:
#                 league_obj = await ingest_league(session, event)
#                 season_obj = await ingest_season(session, event, league_obj.id)
            
#             match_status = event.get("status", {}).get("type", "notstarted")
            
#             # Équipes
#             try:
#                 home_team = await ingest_team(session, api, event["homeTeam"])
#                 away_team = await ingest_team(session, api, event["awayTeam"])
#             except Exception as e:
#                 print(f"  Erreur équipes match {event['id']}: {e}")
#                 continue
            
#             if not home_team or not away_team:
#                 print(f"  Équipes manquantes match {event['id']}, skip")
#                 continue
            
#             # Joueurs
#             try:
#                 await ingest_players_for_team(session, api, event["homeTeam"]["id"], home_team.id)
#                 await ingest_players_for_team(session, api, event["awayTeam"]["id"], away_team.id)
#             except Exception as e:
#                 print(f"  Erreur joueurs: {e}")
            
#             # Managers
#             try:
#                 await ingest_managers_for_fixture(
#                     session, api, event["id"],
#                     event["homeTeam"]["id"], 
#                     event["awayTeam"]["id"]
#                 )
#             except Exception as e:
#                 print(f"  Erreur managers: {e}")

#             # Fixture
#             try:
#                 fixture = await ingest_fixture(
#                     session, event, league_obj.id, season_obj.id,
#                     home_team.id, away_team.id
#                 )
#             except Exception as e:
#                 print(f"  Erreur fixture {event['id']}: {e}")
#                 continue
            
#             # Lineups (si match commencé)
#             if match_status in ["inprogress", "finished"]:
#                 try:
#                     match_obj = Match(api, event["id"])
                    
#                     try:
#                         home_lineups = await match_obj.lineups_home()
#                         if home_lineups:
#                             await ingest_lineups(session, fixture.id, home_lineups, event["homeTeam"]["id"])
#                     except Exception as e:
#                         print(f"  Lineups home indisponibles: {e}")
                    
#                     try:
#                         away_lineups = await match_obj.lineups_away()
#                         if away_lineups:
#                             await ingest_lineups(session, fixture.id, away_lineups, event["awayTeam"]["id"])
#                     except Exception as e:
#                         print(f"  Lineups away indisponibles: {e}")
                        
#                 except Exception as e:
#                     print(f"  Erreur lineups match {event['id']}: {e}")
            
#             # Stats et events (si terminé)
#             if match_status == "finished":
#                 try:
#                     match_obj = Match(api, event["id"])
                    
#                     try:
#                         match_stats = await match_obj.stats()
#                         if match_stats:
#                             await ingest_match_statistics(
#                                 session, fixture.id,
#                                 event["homeTeam"]["id"],
#                                 event["awayTeam"]["id"],
#                                 match_stats
#                             )
#                     except Exception as e:
#                         print(f"  Stats indisponibles: {e}")
                    
#                     try:
#                         match_incidents = await match_obj.incidents()
#                         if match_incidents:
#                             await ingest_match_events(
#                                 session, match_incidents, fixture.id,
#                                 home_team.id, away_team.id
#                             )
#                     except Exception as e:
#                         print(f"  Events indisponibles: {e}")
                        
#                 except Exception as e:
#                     print(f"  Erreur stats/events match {event['id']}: {e}")
            
#         except Exception as e:
#             print(f"  Erreur match {event['id']}: {str(e)}")
#             continue
    
#     return league_obj, season_obj


async def process_round_fixtures(session, api, league_obj, season_obj, match_data):
    
    for event in match_data["events"]:
        try:
            fixture_query = select(Fixture).where(Fixture.sofascore_id == event["id"])
            fixture_result = await session.execute(fixture_query)
            existing_fixture = fixture_result.scalar_one_or_none()
            
            if existing_fixture:
                print(f"  Match {event['id']} déjà ingéré, skip")
                continue
            
            if not league_obj:
                league_obj = await ingest_league(session, event)
                season_obj = await ingest_season(session, event, league_obj.id)
            
            match_status = event.get("status", {}).get("type", "notstarted")
            # print(f"  Match {event['id']} - Status: {match_status}")
            
            # Équipes
            try:
                home_team = await ingest_team(session, api, event["homeTeam"])
                away_team = await ingest_team(session, api, event["awayTeam"])
            except Exception as e:
                print(f" Erreur équipes: {e}")
                continue
            
            if not home_team or not away_team:
                print(f"Équipes manquantes, skip")
                continue
            
            # Joueurs
            try:
                await ingest_players_for_team(session, api, event["homeTeam"]["id"], home_team.id)
                await ingest_players_for_team(session, api, event["awayTeam"]["id"], away_team.id)
            except Exception as e:
                print(f" Erreur joueurs: {e}")
            
            # Managers
            try:
                await ingest_managers_for_fixture(
                    session, api, event["id"],
                    event["homeTeam"]["id"], 
                    event["awayTeam"]["id"]
                )
            except Exception as e:
                print(f"Erreur managers: {e}")

            # Fixture
            try:
                fixture = await ingest_fixture(
                    session, event, league_obj.id, season_obj.id,
                    home_team.id, away_team.id
                )
            except Exception as e:
                print(f"Erreur fixture: {e}")
                continue
            
            # Lineups
            if match_status in ["inprogress", "finished"]:
                try:
                    match_obj = Match(api, event["id"])
                    
                    home_lineups = await match_obj.lineups_home()
                    if home_lineups:
                        await ingest_lineups(session, fixture.id, home_lineups, event["homeTeam"]["id"])
                    
                    away_lineups = await match_obj.lineups_away()
                    if away_lineups:
                        await ingest_lineups(session, fixture.id, away_lineups, event["awayTeam"]["id"])
                        
                except Exception as e:
                    print(f" Lineups indisponibles: {e}")
            
            # Stats et events
            if match_status == "finished":
                try:
                    match_obj = Match(api, event["id"])
                    
                    match_stats = await match_obj.stats()
                    if match_stats:
                        await ingest_match_statistics(
                            session, fixture.id,
                            event["homeTeam"]["id"],
                            event["awayTeam"]["id"],
                            match_stats
                        )
                    
                    match_incidents = await match_obj.incidents()
                    if match_incidents:
                        await ingest_match_events(
                            session, match_incidents, fixture.id,
                            home_team.id, away_team.id
                        )
                        
                except Exception as e:
                    print(f" Stats/events indisponibles: {e}")
            
        except Exception as e:
            print(f" Erreur match {event['id']}: {str(e)}")
            continue
    
    return league_obj, season_obj


async def main():
    api = SofascoreAPI()

    async def fetch_all_competitions(api: SofascoreAPI, competition_names: list[str]) -> dict:
        
        competitions_data = {}

        for name in competition_names:
            try:
                await asyncio.sleep(2)

                search = Search(api, search_string=name)
                result = await search.search_all()
                if not result.get("results"):
                    competitions_data[name] = {}
                    continue

                league_id = result["results"][0]["entity"]["id"]
                league = League(api, league_id)

                # Saisons
                seasons = await league.get_seasons()
                latest_season_id = seasons[0].get("id") if seasons else None

                # Rounds
                rounds_list = []
                if latest_season_id:
                    await asyncio.sleep(1)
                    rounds_data = await league.rounds(latest_season_id)
                    if rounds_data and "rounds" in rounds_data:
                        rounds_list = [r["round"] for r in rounds_data["rounds"]]

                # Classements
                standings_data = None
                if latest_season_id:
                    await asyncio.sleep(1)
                    standings_data = await league.standings(latest_season_id)

                competitions_data[name] = {
                    "league_id": league_id,
                    "seasons": seasons,
                    "latest_season_id": latest_season_id,
                    "rounds": rounds_list,
                    "standings": standings_data,
                    "league_obj": league
                }

            except Exception as e:
                print(f"Erreur lors de la récupération de {name}: {str(e)}")
                competitions_data[name] = {}

        return competitions_data
    
    competitions = [
        # "Africa Cup of Nations",
        "Africa Cup of Nations Qual",
        # "FIFA World Cup",
        # "FIFA World Cup Qual"
    ]

    competitions_data = await fetch_all_competitions(api, competitions)

    async with AsyncSessionLocal() as session:
        try:
            async with session.begin():
                for comp_name, comp_data in competitions_data.items():
                    if not comp_data or not comp_data.get("latest_season_id"):
                        print(f"Pas de données pour {comp_name}")
                        continue

                    league_obj = None
                    season_obj = None
                    latest_season_id = comp_data["latest_season_id"]
                    rounds_list = comp_data["rounds"]
                    league = comp_data["league_obj"]

                    print("\n" + "="*50)
                    print(f" INGESTION {comp_name.upper()}")
                    print("="*50 + "\n")

                    # PHASE DE GROUPES
                    for round_number in rounds_list:
                        try:
                            await asyncio.sleep(1)
                            print(f"\n--- Round {round_number} ---")
                            match_data = await league.league_fixtures_per_round(
                                latest_season_id, round_number
                            )
                            league_obj, season_obj = await process_round_fixtures(
                                session, api, league_obj, season_obj, match_data
                            )
                        except Exception as e:
                            print(f" Erreur round {round_number}: {str(e)}")
                            continue

                    # PHASES FINALES
                    if league_obj and season_obj:
                        await ingest_cup_tree_matches(
                            session, api, latest_season_id,
                            league_obj, season_obj
                        )

                    # CLASSEMENTS
                    # if not season_obj:
                    #     continue
                    # else:
                    standings_data = comp_data["standings"]
                    if standings_data:
                            await ingest_standings(session, standings_data, season_obj.id)
                            print("Classements ingérés avec succès")

                    # STATISTIQUES
                    # print("\n" + "="*50)
                    # print("STATISTIQUES")
                    # print("="*50 + "\n")

                    # async with AsyncSessionLocal() as session:
                    #     first_match_query = select(Fixture).where(
                    #         Fixture.season_id == season_obj.id
                    #     ).order_by(Fixture.date.asc()).limit(1)
                        
                    #     result = await session.execute(first_match_query)
                    #     first_match = result.scalar_one_or_none()
                        
                    #     finished_match_query = select(Fixture).where(
                    #         Fixture.season_id == season_obj.id,
                    #         Fixture.status == "finished"
                    #     ).limit(1)
                        
                    #     result = await session.execute(finished_match_query)
                    #     has_finished_matches = result.scalar_one_or_none()
                        
                    #     if not first_match:
                    #         print(f"Competition pas encore commencée")
                    #     elif not has_finished_matches:
                    #         print("Aucun match terminé, stats pas encore disponibles")
                    #     else:
                    try:
                        await ingest_all_teams_statistics(
                            session, api,
                            comp_data["league_id"], latest_season_id,
                            league_obj.id, season_obj.id
                        )
                    except Exception as e:
                        print(f"Erreur stats équipes: {e}")
                    
                    try:
                        await ingest_all_players_statistics(
                            session, api,
                            comp_data["league_id"], latest_season_id,
                            league_obj.id, season_obj.id
                        )
                    except Exception as e:
                        print(f"Erreur stats joueurs: {e}")

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
